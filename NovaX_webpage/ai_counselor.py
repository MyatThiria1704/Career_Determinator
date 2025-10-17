import os
import google.generativeai as genai
from django.conf import settings
import json
import random
from time import sleep
import google.api_core.exceptions
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationalCounselor:
    def __init__(self):
        # Retrieve API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set. Falling back to rule-based responses.")
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            # Verify available models
            available_models = [model.name for model in genai.list_models()]
            logger.info(f"Available Gemini models: {available_models}")
            if 'models/gemini-pro' not in available_models:
                logger.error("Model 'gemini-pro' not available. Falling back to rule-based responses.")
                self.model = None
                return
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Gemini AI Connected Successfully!")
        except Exception as e:
            logger.error(f"❌ Gemini AI setup failed: {str(e)}")
            self.model = None
    
    def get_initial_greeting(self):
        """Return initial greeting message with human touch"""
        greetings = [
            "👋 Hello there! I'm Alex, your AI Education Counselor. I'm here to help you discover career paths that truly match who you are. Let's get to know each other better!",
            "🌟 Welcome! I'm Dr. Evans, your virtual career guide. I'll help you uncover exciting career possibilities based on your unique personality and strengths. Ready to begin our journey?",
            "💫 Hi! I'm Sophia, your career companion. Think of me as your personal guide to finding work that doesn't just pay the bills, but fulfills you. Shall we start exploring together?"
        ]
        
        return {
            "message": random.choice(greetings),
            "next_question": "Let's begin with understanding your work style. On a scale of 1-10, how would you rate your natural tendency to be organized and pay attention to details?",
            "field": "C_score",
            "conversation_step": "personality",
            "show_edit_option": False
        }
    
    def process_answer(self, user_input, current_field, conversation_step, collected_data):
        """Process user's answer and determine next question"""
        
        # Check if user wants to edit previous answers
        if self._is_edit_request(user_input):
            return self._handle_edit_request(user_input, collected_data)
        
        # Validate numeric answer if not in edit mode
        if not self._is_edit_mode(conversation_step) and not self._is_valid_score(user_input):
            human_responses = [
                "I appreciate your input! Could you give me a number between 1 and 10? This helps me understand you better.",
                "Thanks for sharing! To make sure I get this right, could you rate that on a scale of 1 to 10?",
                "I want to make sure I understand correctly. Could you give me a number from 1 (lowest) to 10 (highest)?"
            ]
            return {
                "message": random.choice(human_responses),
                "next_question": self._get_current_question(current_field),
                "field": current_field,
                "conversation_step": conversation_step,
                "show_edit_option": len(collected_data) > 0,
                "completed": False
            }
        
        # If we have AI model, use it for more natural conversation
        if self.model and len(collected_data) > 2 and not self._is_edit_mode(conversation_step):
            try:
                return self._ai_enhanced_response(user_input, current_field, conversation_step, collected_data)
            except Exception as e:
                logger.error(f"AI response failed: {str(e)}. Falling back to rule-based response.")
                return self._rule_based_next_question(user_input, current_field, conversation_step, collected_data)
        
        # Rule-based flow
        return self._rule_based_next_question(user_input, current_field, conversation_step, collected_data)
    
    def _is_edit_request(self, user_input):
        """Check if user wants to edit previous answers"""
        edit_keywords = ['edit', 'change', 'modify', 'back', 'previous', 'correction', 'mistake', 'wrong', 'go back']
        return any(keyword in user_input.lower() for keyword in edit_keywords)
    
    def _is_edit_mode(self, conversation_step):
        """Check if currently in edit mode"""
        return conversation_step.startswith("editing")
    
    def _is_valid_score(self, user_input):
        """Check if input is a valid score between 1-10"""
        try:
            score = float(user_input)
            return 1 <= score <= 10
        except ValueError:
            return False
    
    def _handle_edit_request(self, user_input, collected_data):
        """Handle user's request to edit previous answers"""
        if not collected_data:
            no_data_responses = [
                "We haven't started our assessment yet! Let's begin with the first question.",
                "You're eager to get things right! Let's start from the beginning first.",
                "We'll build your profile together. Let me ask you the first question."
            ]
            return {
                "message": random.choice(no_data_responses),
                "next_question": self._get_current_question("C_score"),
                "field": "C_score",
                "conversation_step": "personality",
                "show_edit_option": False,
                "completed": False
            }
        
        # Create list of answered questions for editing
        edit_options = []
        field_descriptions = self._get_field_descriptions()
        
        for field, score in collected_data.items():
            description = field_descriptions.get(field, field)
            edit_options.append(f"• {description}: {score}/10")
        
        edit_list = "\n".join(edit_options)
        
        edit_responses = [
            "Of course! We can review your previous answers. Here's what you've shared so far:",
            "Happy to help you make adjustments! Here are your current responses:",
            "Let's fine-tune your profile. Here are your answers up to now:"
        ]
        
        return {
            "message": random.choice(edit_responses),
            "next_question": f"{edit_list}\n\nWhich aspect would you like to update? You can say the name (like 'organization' or 'teamwork') or type the number.",
            "field": "edit_mode",
            "conversation_step": "editing",
            "show_edit_option": False,
            "edit_options": list(collected_data.keys()),
            "completed": False
        }
    
    def _get_field_descriptions(self):
        """Get human-readable descriptions for fields"""
        return {
            "C_score": "Organization & Attention to Detail",
            "O_score": "Openness to New Experiences",
            "E_score": "Outgoing & Social Nature", 
            "A_score": "Cooperation & Team Spirit",
            "N_score": "Stress Management & Resilience",
            "Numerical_Aptitude": "Comfort with Numbers & Math",
            "Verbal_Aptitude": "Language & Communication Skills",
            "Abstract_Reasoning": "Pattern Recognition Ability",
            "Logical_Reasoning": "Logical Thinking Skills",
            "Spatial_Aptitude": "Spatial Visualization",
            "Enjoy_Teamwork": "Enjoyment of Team Collaboration",
            "Creative_Thinking": "Creative Problem-Solving",
            "Attention_to_Detail": "Focus on Details"
        }
    
    def _get_current_question(self, current_field):
        """Get the current question text"""
        questions_flow = self._get_questions_flow()
        for field, step, question in questions_flow:
            if field == current_field:
                return question
        return "Please continue with our assessment."
    
    def _process_edit_field_selection(self, user_input, collected_data):
        """Process user's selection of which field to edit"""
        field_to_edit = self._find_field_by_input(user_input, collected_data)
        
        if field_to_edit:
            field_descriptions = self._get_field_descriptions()
            description = field_descriptions.get(field_to_edit, field_to_edit)
            previous_score = collected_data[field_to_edit]
            
            edit_confirmations = [
                f"Updating {description}. You previously rated this {previous_score}/10.",
                f"Let's update your {description}. Your current rating is {previous_score}/10.",
                f"Adjusting {description}. Your earlier response was {previous_score}/10."
            ]
            
            question = self._get_question_for_field(field_to_edit)
            return {
                "message": random.choice(edit_confirmations),
                "next_question": question,
                "field": f"editing_{field_to_edit}",
                "conversation_step": "editing_field",
                "show_edit_option": False,
                "field_to_edit": field_to_edit,
                "completed": False
            }
        else:
            field_descriptions = self._get_field_descriptions()
            available_options = []
            for i, field in enumerate(collected_data.keys(), 1):
                desc = field_descriptions.get(field, field)
                available_options.append(f"{i}. {desc}")
            
            options_text = "\n".join(available_options)
            
            clarification_responses = [
                "I want to make sure I get this right. Which area would you like to update?",
                "Let me clarify which aspect you'd like to adjust:",
                "Which specific area would you like to change?"
            ]
            
            return {
                "message": random.choice(clarification_responses),
                "next_question": f"Available options:\n{options_text}\n\nPlease choose by number or name:",
                "field": "edit_mode",
                "conversation_step": "editing",
                "show_edit_option": False,
                "edit_options": list(collected_data.keys()),
                "completed": False
            }
    
    def _find_field_by_input(self, user_input, collected_data):
        """Find field based on user input (number or text)"""
        user_input = user_input.lower().strip()
        field_descriptions = self._get_field_descriptions()
        
        # Check if input is a number
        try:
            index = int(user_input) - 1
            fields = list(collected_data.keys())
            if 0 <= index < len(fields):
                return fields[index]
        except ValueError:
            pass
        
        # Check if input matches field names or descriptions
        for field in collected_data.keys():
            if (user_input in field.lower() or 
                any(word in user_input for word in field_descriptions[field].lower().split())):
                return field
        
        return None
    
    def _get_question_for_field(self, field):
        """Get the question text for a specific field"""
        questions = {
            "C_score": "How organized and detail-oriented are you? (1 = very disorganized, 10 = extremely organized)",
            "O_score": "How open are you to new experiences and ideas? (1 = prefer routine, 10 = love trying new things)",
            "E_score": "How outgoing and sociable are you? (1 = very reserved, 10 = extremely outgoing)",
            "A_score": "How cooperative and compassionate are you? (1 = very competitive, 10 = extremely cooperative)",
            "N_score": "How do you handle stress and negative emotions? (1 = very sensitive, 10 = very resilient)",
            "Numerical_Aptitude": "How comfortable are you with numbers and calculations? (1 = struggle with math, 10 = excel at math)",
            "Verbal_Aptitude": "How strong are your language and communication skills? (1 = struggle with words, 10 = excellent communicator)",
            "Abstract_Reasoning": "How well can you identify patterns and solve abstract problems? (1 = find it difficult, 10 = very skilled)",
            # "Logical_Reasoning": "How good are you at logical thinking and reasoning? (1 = struggle with logic, 10 = very logical)",
            "Perceptual_Aptitude" : "How easily can you recognize patterns or spot something that looks “off” in a group of similar items? (1 = often miss details, 10 = highly observant)",
            "Spatial_Aptitude": "How well can you visualize and manipulate objects in space? (1 = poor spatial sense, 10 = excellent spatial thinking)",
            "Enjoy_Teamwork": "How much do you enjoy working in teams? (1 = prefer working alone, 10 = love team collaboration)",
            "Creative_Thinking": "How creative are you in problem-solving? (1 = prefer standard solutions, 10 = highly innovative)",
            "Attention_to_Detail": "How important is attention to detail in your work? (1 = overlook details, 10 = extremely detail-oriented)"
        }
        return questions.get(field, f"Please rate your {field.replace('_', ' ').lower()}")
    # def _get_question_for_field(self, field):
    #     """Get the question text for a specific field"""
    #     questions = {
    #         "C_score": "How organized and detail-oriented are you? (1 = very disorganized, 10 = extremely organized)",
    #         "O_score": "How open are you to new experiences and ideas? (1 = prefer routine, 10 = love trying new things)",
    #         "E_score": "How outgoing and sociable are you? (1 = very reserved, 10 = extremely outgoing)",
    #         "A_score": "How cooperative and compassionate are you? (1 = very competitive, 10 = extremely cooperative)",
    #         "N_score": "How do you handle stress and negative emotions? (1 = very sensitive, 10 = very resilient)",
    #         "Numerical_Aptitude": "How comfortable are you with numbers and calculations? (1 = struggle with math, 10 = excel at math)",
    #         "Spatial_Aptitude": "How well can you visualize and manipulate objects in space? (1 = poor spatial sense, 10 = excellent spatial thinking)",
    #         "Perceptual_Aptitude": "How good are you at noticing details and visual accuracy? (1 = often miss details, 10 = highly observant)",
    #         "Abstract_Reasoning": "How well can you identify patterns and solve abstract problems? (1 = find it difficult, 10 = very skilled)",
    #         "Verbal_Aptitude": "How strong are your language and communication skills? (1 = struggle with words, 10 = excellent communicator)",
    #         "Enjoy_Teamwork": "How much do you enjoy working in teams? (1 = prefer working alone, 10 = love team collaboration)",
    #         "Creative_Thinking": "How creative are you in problem-solving? (1 = prefer standard solutions, 10 = highly innovative)",
    #         "Attention_to_Detail": "How important is attention to detail in your work? (1 = overlook details, 10 = extremely detail-oriented)"
    #     }
    #     return questions.get(field, f"Please rate your {field.replace('_', ' ').lower()}")
    
    def _process_edit_answer(self, user_input, field_to_edit, collected_data):
        """Process the new answer for an edited field"""
        if not self._is_valid_score(user_input):
            question = self._get_question_for_field(field_to_edit)
            return {
                "message": "Let's try that again with a number between 1 and 10:",
                "next_question": question,
                "field": f"editing_{field_to_edit}",
                "conversation_step": "editing_field",
                "show_edit_option": False,
                "field_to_edit": field_to_edit,
                "completed": False
            }
        
        # Update the score
        collected_data[field_to_edit] = float(user_input)
        field_descriptions = self._get_field_descriptions()
        description = field_descriptions.get(field_to_edit, field_to_edit)
        
        update_responses = [
            f"✅ Perfect! I've updated your {description} to {user_input}/10.",
            f"✅ Got it! Your {description} is now {user_input}/10.",
            f"✅ Updated! {description}: {user_input}/10."
        ]
        
        # Find the next question to continue from
        next_field = self._get_next_field_after_edit(field_to_edit, collected_data)
        
        if next_field:
            question = self._get_current_question(next_field)
            return {
                "message": random.choice(update_responses) + " Let's continue where we left off...",
                "next_question": question,
                "field": next_field,
                "conversation_step": self._get_step_for_field(next_field),
                "show_edit_option": True,
                "completed": False
            }
        else:
            # All questions completed after edit
            completion_responses = [
                "Excellent! With your updates, I now have a complete picture of your unique profile.",
                "Wonderful! Your updated responses give me everything I need to analyze your career matches.",
                "Perfect! I've incorporated your changes and now have a comprehensive view of your strengths."
            ]
            return {
                "message": random.choice(completion_responses) + " Let me analyze your profile and suggest suitable career paths...",
                "next_question": None,
                "field": None,
                "conversation_step": "completed",
                "show_edit_option": False,
                "completed": True
            }
    
    def _get_next_field_after_edit(self, edited_field, collected_data):
        """Determine which field to ask next after editing"""
        questions_flow = self._get_questions_flow()
        current_index = None
        
        # Find the position of the edited field
        for i, (field, step, question) in enumerate(questions_flow):
            if field == edited_field:
                current_index = i
                break
        
        if current_index is None:
            return None
        
        # Find the next unanswered question
        for i in range(current_index + 1, len(questions_flow)):
            next_field, next_step, next_question = questions_flow[i]
            if next_field not in collected_data:
                return next_field
        
        # All questions after the edited one are answered
        return None
    
    def _get_step_for_field(self, field):
        """Get the conversation step for a field"""
        questions_flow = self._get_questions_flow()
        for f, step, question in questions_flow:
            if f == field:
                return step
        return "personality"
    
    def _rule_based_next_question(self, user_input, current_field, conversation_step, collected_data):
        """Rule-based question flow with human touch"""
        # Handle edit mode cases
        if conversation_step == "editing":
            return self._process_edit_field_selection(user_input, collected_data)
        
        elif conversation_step == "editing_field" and current_field.startswith("editing_"):
            field_to_edit = current_field.replace("editing_", "")
            return self._process_edit_answer(user_input, field_to_edit, collected_data)
        
        # Normal question flow - store the answer
        if current_field and not current_field.startswith("editing_"):
            collected_data[current_field] = float(user_input)
        
        questions_flow = self._get_questions_flow()
        
        # Find current position and get next question
        current_index = None
        for i, (field, step, question) in enumerate(questions_flow):
            if field == current_field:
                current_index = i
                break
        
        if current_index is not None and current_index < len(questions_flow) - 1:
            next_field, next_step, next_question = questions_flow[current_index + 1]
            
            # Generate human-like acknowledgment
            acknowledgments = [
                f"Thanks for sharing! {user_input}/10 gives me good insight.",
                f"I appreciate your honesty! {user_input}/10 helps me understand you better.",
                f"Noted! {user_input}/10 - that's helpful information.",
                f"Thank you! Rating of {user_input}/10 is very informative."
            ]
            
            # Add contextual comments based on score
            score = float(user_input)
            if score >= 8:
                contextual = " That's quite strong!"
            elif score <= 3:
                contextual = " That's good to know for our assessment."
            else:
                contextual = ""
            
            return {
                "message": random.choice(acknowledgments) + contextual,
                "next_question": next_question,
                "field": next_field,
                "conversation_step": next_step,
                "show_edit_option": True,
                "completed": False
            }
        else:
            # All questions completed
            completion_responses = [
                "Excellent! I have all the information I need to understand your unique profile.",
                "Wonderful! Your responses have given me a clear picture of your strengths and preferences.",
                "Perfect! I now have a comprehensive view of what makes you unique."
            ]
            return {
                "message": random.choice(completion_responses) + " Let me analyze everything and suggest career paths that align with who you are...",
                "next_question": None,
                "field": None,
                "conversation_step": "completed",
                "show_edit_option": False,
                "completed": True
            }
    
    def _get_questions_flow(self):
        """Define the order of questions with natural transitions"""
        return [
            # Personality Questions (Big Five)
            ("C_score", "personality", "On a scale of 1-10, how organized and detail-oriented are you? (1 = very disorganized, 10 = extremely organized)"),
            ("O_score", "personality", "How open are you to new experiences and ideas? (1 = prefer routine and familiarity, 10 = love exploring new possibilities)"),
            ("E_score", "personality", "How outgoing and sociable would you describe yourself? (1 = more reserved and private, 10 = highly outgoing and social)"),
            ("A_score", "personality", "How cooperative and compassionate are you in your interactions? (1 = more competitive and direct, 10 = highly cooperative and empathetic)"),
            ("N_score", "personality", "How do you typically handle stress and challenging emotions? (1 = quite sensitive to stress, 10 = very resilient and calm under pressure)"),
            
            # Aptitude Questions with transition
            # ("Numerical_Aptitude", "aptitude", "Now let's explore your natural abilities. How comfortable are you working with numbers and calculations? (1 = avoid math when possible, 10 = enjoy and excel at mathematical tasks)"),
            # ("Verbal_Aptitude", "aptitude", "How strong are your language and communication skills? (1 = struggle with expressing ideas, 10 = excellent at communication and language)"),
            # ("Abstract_Reasoning", "aptitude", "How easily can you identify patterns and solve abstract problems? (1 = find abstract thinking challenging, 10 = very skilled at pattern recognition)"),
            # ("Logical_Reasoning", "aptitude", "How natural is logical thinking and reasoning for you? (1 = prefer intuitive approaches, 10 = highly logical and analytical)"),
            # ("Spatial_Aptitude", "aptitude", "How well can you visualize and manipulate objects in space? (1 = poor spatial awareness, 10 = excellent spatial thinking)"),
            ("Numerical_Aptitude", "aptitude", "How comfortable are you with numbers and calculations?"),
            ("Verbal_Aptitude", "aptitude", "How strong are your language and communication skills?"),
            ("Abstract_Reasoning", "aptitude", "How easily can you identify patterns and solve abstract problems?"),
            ("Perceptual_Aptitude", "aptitude", "How quickly do you notice small differences or errors in what you see or read?"),  # Add this
            ("Spatial_Aptitude", "aptitude", "How well can you visualize and manipulate objects in space?"),
            
            # Work Preference Questions with transition
            ("Enjoy_Teamwork", "preference", "Now about your work style preferences: How much do you enjoy collaborating in teams? (1 = strongly prefer working independently, 10 = thrive in team environments)"),
            ("Creative_Thinking", "preference", "How would you rate your creative problem-solving approach? (1 = prefer established methods, 10 = highly innovative and creative)"),
            ("Attention_to_Detail", "preference", "Finally, how important is attention to detail in your ideal work? (1 = prefer big-picture thinking, 10 = extremely detail-oriented and precise)")
        ]
    
    def _ai_enhanced_response(self, user_input, current_field, conversation_step, collected_data):
        """Use AI to generate more natural responses with retry logic"""
        prompt = f"""
        You are a warm, empathetic educational counselor named Alex having a natural conversation with a student. 
        So far you've collected these ratings (1-10 scale): {collected_data}
        
        The student just answered: "{user_input}" for question about {current_field}
        
        Provide a natural, human-like response that:
        - Acknowledges their answer warmly
        - Shows genuine interest in understanding them
        - Gently transitions to the next question
        - Mentions they can say 'edit' if they want to change previous answers
        
        Keep it conversational and friendly. Return your response in JSON format:
        {{
            "message": "your warm acknowledgment here",
            "next_question": "next natural question here", 
            "field": "next_field_name",
            "conversation_step": "personality/aptitude/preference",
            "show_edit_option": true
        }}
        """
        
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                response = self.model.generate_content(prompt)
                return json.loads(response.text)
            except google.api_core.exceptions.ResourceExhausted:
                attempt += 1
                logger.warning(f"Rate limit hit, retrying attempt {attempt}/{max_attempts}")
                sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"AI response failed: {str(e)}")
                raise
        logger.error("Max retry attempts exceeded for AI response")
        raise Exception("Failed to generate AI response after retries")

# Global instance
counselor = EducationalCounselor()