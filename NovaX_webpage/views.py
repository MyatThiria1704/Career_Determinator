# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse

from django.utils.crypto import get_random_string

from .models import CareerSurvey, PublicUniversity, PrivateCollege, Career, Category
from .form import StudentProfileForm
from .models import StudentProfile
from .send_email import send_email
from django.core.paginator import Paginator
from django.db.models import Q
from .models import AppReview
from .form import AppReviewForm
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import CareerSurvey
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.utils.crypto import get_random_string
from .send_email import send_email
from django.conf import settings
from .ai_counselor import counselor
import pickle
import numpy as np
import google.generativeai as genai
import os
# ====================================================
# 🔹 Career Prediction View
# ====================================================

# ... your existing imports and model loading code ...
# Add these imports at the top
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import base64
from datetime import datetime
# views.py - Add this import at the top with other imports
from .models import QuizAttempt, QuestionResponse, CareerSurvey, PublicUniversity, PrivateCollege, Career, Category, StudentProfile, AppReview

# Add this function to your views.py
@csrf_exempt
@require_POST
def download_career_report(request):
    """Generate and download a PDF career report"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        predictions = data.get('predictions', [])
        counseling_data = request.session.get('counseling_data', {})
        conversation_history = request.session.get('conversation_history', [])
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.5*inch, rightMargin=0.5*inch)
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0c4a6e'),
            spaceAfter=30,
            alignment=1  # Center aligned
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0369a1'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155'),
            spaceAfter=12
        )
        
        # Build the story (content)
        story = []
        
        # Header
        story.append(Paragraph("NovaX Career Intelligence Report", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                             ParagraphStyle('Date', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.gray)))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary_text = """
        This comprehensive career assessment analyzes your personality traits, aptitudes, and work preferences 
        to identify career paths where you're most likely to excel and find fulfillment. The recommendations 
        are based on psychological research and data-driven analysis of successful professionals.
        """
        story.append(Paragraph(summary_text, normal_style))
        story.append(Spacer(1, 15))
        
        # Top Career Recommendations
        story.append(Paragraph("Top Career Recommendations", heading_style))
        
        if predictions:
            # Create table for predictions
            prediction_data = [['Rank', 'Career Path', 'Match Score', 'Key Strengths']]
            
            strength_mapping = {
                'C_score': 'Organization & Detail-Oriented',
                'O_score': 'Openness to Innovation',
                'E_score': 'Social & Communication Skills', 
                'A_score': 'Team Collaboration',
                'N_score': 'Stress Resilience',
                'Numerical_Aptitude': 'Analytical Thinking',
                'Verbal_Aptitude': 'Communication Excellence',
                'Abstract_Reasoning': 'Problem-Solving',
                'Logical_Reasoning': 'Logical Analysis',
                'Spatial_Aptitude': 'Spatial Intelligence',
                'Enjoy_Teamwork': 'Collaborative Spirit',
                'Creative_Thinking': 'Creative Innovation',
                'Attention_to_Detail': 'Precision Focus'
            }
            
            for i, pred in enumerate(predictions[:3], 1):
                # Determine top 3 strengths for this career
                strengths = get_strengths_for_career(counseling_data)
                strength_text = ", ".join(strengths[:3])
                
                prediction_data.append([
                    str(i),
                    pred['career'],
                    f"{pred['probability']}%",
                    strength_text
                ])
            
            # Create and style the table
            table = Table(prediction_data, colWidths=[0.6*inch, 2.2*inch, 0.8*inch, 2.4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0c4a6e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("No career predictions available.", normal_style))
        
        story.append(Spacer(1, 20))
        
        # Personal Profile Analysis
        story.append(Paragraph("Personal Profile Analysis", heading_style))
        
        # Personality Insights
        personality_data = [
            ['Trait', 'Score', 'Interpretation'],
            ['Organization (C)', counseling_data.get('C_score', 'N/A'), get_interpretation('C_score', counseling_data.get('C_score'))],
            ['Openness (O)', counseling_data.get('O_score', 'N/A'), get_interpretation('O_score', counseling_data.get('O_score'))],
            ['Extraversion (E)', counseling_data.get('E_score', 'N/A'), get_interpretation('E_score', counseling_data.get('E_score'))],
            ['Agreeableness (A)', counseling_data.get('A_score', 'N/A'), get_interpretation('A_score', counseling_data.get('A_score'))],
            ['Neuroticism (N)', counseling_data.get('N_score', 'N/A'), get_interpretation('N_score', counseling_data.get('N_score'))]
        ]
        
        personality_table = Table(personality_data, colWidths=[1.5*inch, 0.7*inch, 3.8*inch])
        personality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        
        story.append(personality_table)
        story.append(Spacer(1, 15))
        
        # Aptitude Scores
        story.append(Paragraph("Aptitude Assessment", ParagraphStyle('SubHeading', parent=heading_style, fontSize=14)))
        
        aptitude_data = [
            ['Aptitude', 'Score', 'Level'],
            ['Numerical Reasoning', counseling_data.get('Numerical_Aptitude', 'N/A'), get_level(counseling_data.get('Numerical_Aptitude'))],
            ['Verbal Ability', counseling_data.get('Verbal_Aptitude', 'N/A'), get_level(counseling_data.get('Verbal_Aptitude'))],
            ['Abstract Thinking', counseling_data.get('Abstract_Reasoning', 'N/A'), get_level(counseling_data.get('Abstract_Reasoning'))],
            ['Logical Reasoning', counseling_data.get('Logical_Reasoning', 'N/A'), get_level(counseling_data.get('Logical_Reasoning'))],
            ['Spatial Awareness', counseling_data.get('Spatial_Aptitude', 'N/A'), get_level(counseling_data.get('Spatial_Aptitude'))]
        ]
        
        aptitude_table = Table(aptitude_data, colWidths=[1.8*inch, 0.7*inch, 1.5*inch])
        aptitude_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f9ff')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd'))
        ]))
        
        story.append(aptitude_table)
        story.append(Spacer(1, 20))
        
        # Work Style Preferences
        story.append(Paragraph("Work Style Preferences", heading_style))
        
        preference_text = f"""
        Your assessment indicates a strong preference for {get_work_style_preference(counseling_data)}. 
        You thrive in environments that emphasize {get_environment_preference(counseling_data)}.
        """
        story.append(Paragraph(preference_text, normal_style))
        
        # Next Steps
        story.append(Paragraph("Recommended Next Steps", heading_style))
        next_steps = """
        1. Research the top recommended career paths in depth
        2. Connect with professionals in these fields for informational interviews
        3. Identify relevant skills to develop or enhance
        4. Consider internship or shadowing opportunities
        5. Discuss these findings with a career counselor or mentor
        """
        story.append(Paragraph(next_steps, normal_style))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = """
        <i>This report was generated by NovaX Career Intelligence AI System. 
        The recommendations are based on statistical analysis and should be considered 
        alongside personal interests, values, and market conditions.</i>
        """
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Italic'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF value and create response
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"novax_career_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return JsonResponse({'error': 'Failed to generate report'}, status=500)

# Helper functions for the PDF generation
def get_interpretation(trait, score):
    """Get interpretation for personality traits"""
    if score is None:
        return "Not assessed"
    
    score = float(score)
    interpretations = {
        'C_score': {
            'low': "Flexible and adaptable approach",
            'medium': "Balanced organization skills", 
            'high': "Highly structured and systematic"
        },
        'O_score': {
            'low': "Prefer routine and consistency",
            'medium': "Open to new experiences",
            'high': "Highly innovative and curious"
        },
        'E_score': {
            'low': "Reflective and reserved",
            'medium': "Socially balanced",
            'high': "Outgoing and energetic"
        },
        'A_score': {
            'low': "Independent and direct",
            'medium': "Cooperative and considerate",
            'high': "Highly empathetic and supportive"
        },
        'N_score': {
            'low': "Emotionally resilient",
            'medium': "Generally stable",
            'high': "Sensitive and emotionally aware"
        }
    }
    
    if score <= 4:
        level = 'low'
    elif score <= 7:
        level = 'medium'
    else:
        level = 'high'
        
    return interpretations.get(trait, {}).get(level, "Average")

def get_level(score):
    """Get proficiency level for aptitudes"""
    if score is None:
        return "Not assessed"
    
    score = float(score)
    if score <= 3:
        return "Basic"
    elif score <= 6:
        return "Intermediate"
    elif score <= 8:
        return "Advanced"
    else:
        return "Expert"

def get_strengths_for_career(counseling_data):
    """Identify top strengths based on assessment scores"""
    strength_scores = []
    for field, score in counseling_data.items():
        if score is not None:
            strength_scores.append((field, float(score)))
    
    # Sort by score descending and return top strengths
    strength_scores.sort(key=lambda x: x[1], reverse=True)
    return [field for field, score in strength_scores[:5]]

def get_work_style_preference(counseling_data):
    """Determine work style preference"""
    teamwork = counseling_data.get('Enjoy_Teamwork', 5)
    creativity = counseling_data.get('Creative_Thinking', 5)
    detail = counseling_data.get('Attention_to_Detail', 5)
    
    if teamwork >= 8:
        return "collaborative team environments"
    elif creativity >= 8:
        return "innovative and creative work"
    elif detail >= 8:
        return "detailed and precise tasks"
    else:
        return "balanced and varied work"

def get_environment_preference(counseling_data):
    """Determine preferred work environment"""
    extraversion = counseling_data.get('E_score', 5)
    openness = counseling_data.get('O_score', 5)
    
    if extraversion >= 7 and openness >= 7:
        return "dynamic, social, and innovative settings"
    elif extraversion >= 7:
        return "social and interactive environments"
    elif openness >= 7:
        return "creative and changing circumstances"
    else:
        return "stable and predictable settings"
    
    
@csrf_exempt
@require_POST
def start_counseling(request):
    """Start a new counseling session"""
    try:
        initial_data = counselor.get_initial_greeting()
        
        # Initialize session
        request.session['counseling_data'] = {}
        request.session['conversation_history'] = []
        request.session['current_field'] = initial_data['field']
        request.session['conversation_step'] = initial_data['conversation_step']
        
        # Log first message
        request.session['conversation_history'].append({
            'type': 'bot',
            'message': initial_data['message']
        })
        request.session['conversation_history'].append({
            'type': 'bot',
            'message': initial_data['next_question']
        })
        
        return JsonResponse({
            'success': True,
            'message': initial_data['message'],
            'next_question': initial_data['next_question'],
            'field': initial_data['field'],
            'conversation_step': initial_data['conversation_step']
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
@csrf_exempt
@require_POST
def process_counseling_answer(request):
    """Process user's answer during counseling session"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_answer = data.get('answer')
        current_field = request.session.get('current_field')
        counseling_data = request.session.get('counseling_data', {})
        conversation_step = request.session.get('conversation_step', 'personality')
        
        # Log user message
        conversation_history = request.session.get('conversation_history', [])
        
        # Only log if it's not a simple edit command we're handling
        if not (user_answer.lower() in ['edit', 'change', 'back'] and conversation_step != 'editing'):
            conversation_history.append({
                'type': 'user',
                'message': user_answer
            })
        
        # Get next question from counselor
        counselor_response = counselor.process_answer(
            user_answer, current_field, conversation_step, counseling_data
        )
        
        # Update session data
        request.session['counseling_data'] = counseling_data
        request.session['current_field'] = counselor_response.get('field')
        request.session['conversation_step'] = counselor_response.get('conversation_step')
        
        # Log bot responses
        if counselor_response.get('message'):
            conversation_history.append({
                'type': 'bot', 
                'message': counselor_response['message']
            })
        if counselor_response.get('next_question'):
            conversation_history.append({
                'type': 'bot',
                'message': counselor_response['next_question']
            })
        
        request.session['conversation_history'] = conversation_history
        request.session.modified = True
        
        response_data = {
            'success': True,
            'message': counselor_response.get('message', ''),
            'next_question': counselor_response.get('next_question'),
            'field': counselor_response.get('field'),
            'conversation_step': counselor_response.get('conversation_step'),
            'completed': counselor_response.get('completed', False),
            'show_edit_option': counselor_response.get('show_edit_option', True),
            'collected_data': counseling_data
        }
        
        # Add edit options if in edit mode
        if counselor_response.get('edit_options'):
            response_data['edit_options'] = counselor_response['edit_options']
        
        # If counseling is completed, make prediction
    #     if counselor_response.get('completed'):
    #         predictions = generate_career_predictions(counseling_data)
    #         response_data['predictions'] = predictions
            
    #         # Save the session data
    #         save_counseling_session(request, counseling_data, predictions)
        
    #     return JsonResponse(response_data)
        
    # except Exception as e:
    #     return JsonResponse({'error': str(e)}, status=400)
        if counselor_response.get('completed'):
            predictions = generate_career_predictions(counseling_data)
            response_data['predictions'] = predictions
            
            # Save the session data
            save_counseling_session(request, counseling_data, predictions)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# def generate_career_predictions(counseling_data):
#     """Generate career predictions from collected data"""
#     if not ENSEMBLE_MODELS:
#         return None
    
#     try:
#         features = [
#             "O_score", "C_score", "E_score", "A_score", "N_score",
#             "Numerical_Aptitude", "Verbal_Aptitude", "Abstract_Reasoning", 
#             "Logical_Reasoning", "Spatial_Aptitude",
#             "Enjoy_Teamwork", "Creative_Thinking", "Attention_to_Detail"
#         ]
        
#         # Ensure all features are present, use 5 as default for missing values
#         input_data = [float(counseling_data.get(feat, 5)) for feat in features]
        
#         # Scale and predict
#         input_array = np.array(input_data).reshape(1, -1)
#         scaled_input = SCALER.transform(input_array)
        
#         # Ensemble prediction
#         probas_list = [model.predict_proba(scaled_input) for model in ENSEMBLE_MODELS]
#         avg_probas = np.mean(probas_list, axis=0)
        
#         # Get top 3 predictions
#         top3_indices = np.argsort(avg_probas[0])[::-1][:3]
#         top3_careers = LABEL_ENCODER.inverse_transform(top3_indices)
        
#         results = []
#         for career, index in zip(top3_careers, top3_indices):
#             probability = avg_probas[0][index]
#             results.append({
#                 'career': career,
#                 'probability': round(probability * 100, 2)
#             })
            
#         return results
        
#     except Exception as e:
#         print(f"Prediction error: {e}")
#         return None

def generate_career_predictions(counseling_data):
    """Generate career predictions from collected data"""
    if not ENSEMBLE_MODELS:
        return None
    
    try:
        # Use the EXACT features your model was trained on
        features = [
            "O_score", "C_score", "E_score", "A_score", "N_score",
            "Numerical Aptitude", "Spatial Aptitude", "Perceptual Aptitude", 
            "Abstract Reasoning", "Verbal Reasoning",
            "Enjoy_Teamwork", "Creative_Thinking", "Attention_to_Detail"
        ]
        
        # Map from collected data to expected features
        feature_mapping = {
            "Numerical Aptitude": "Numerical_Aptitude",
            "Spatial Aptitude": "Spatial_Aptitude", 
            "Perceptual Aptitude": None,  # Not currently collected
            "Abstract Reasoning": "Abstract_Reasoning",
            "Verbal Reasoning": "Verbal_Aptitude",
            # Other features have the same names
        }
        
        # Ensure all features are present
        input_data = []
        for feat in features:
            if feat in feature_mapping and feature_mapping[feat]:
                # Use mapped feature name
                mapped_feat = feature_mapping[feat]
                input_data.append(float(counseling_data.get(mapped_feat, 5)))
            elif feat in feature_mapping and feature_mapping[feat] is None:
                # For Perceptual Aptitude (not collected), use default
                input_data.append(5.0)
            else:
                # Use direct feature name
                input_data.append(float(counseling_data.get(feat, 5)))
        
        # Scale and predict
        input_array = np.array(input_data).reshape(1, -1)
        scaled_input = SCALER.transform(input_array)
        
        # Ensemble prediction
        probas_list = [model.predict_proba(scaled_input) for model in ENSEMBLE_MODELS]
        avg_probas = np.mean(probas_list, axis=0)
        
        # Get top 3 predictions
        top3_indices = np.argsort(avg_probas[0])[::-1][:3]
        top3_careers = LABEL_ENCODER.inverse_transform(top3_indices)
        
        results = []
        for career, index in zip(top3_careers, top3_indices):
            probability = avg_probas[0][index]
            results.append({
                'career': career,
                'probability': round(probability * 100, 2)
            })
            
        return results
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

# def save_counseling_session(request, counseling_data, predictions):
#     """Save counseling session to database"""
#     try:
#         from .models import CareerSurvey  # Your existing model
        
#         CareerSurvey.objects.create(
#             category='AI_Counseling',
#             responses={
#                 'counseling_data': counseling_data,
#                 'predictions': predictions,
#                 'conversation_history': request.session.get('conversation_history', [])
#             }
#         )
#     except Exception as e:
#         print(f"Error saving counseling session: {e}")

# views.py - Update the counseling completion handler

def save_counseling_session(request, counseling_data, predictions):
    """Save counseling session to database"""
    try:
        # Create QuizAttempt
        quiz_attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz_type='AI_COUNSELING',
            completed_at=timezone.now(),
            conversation_data=request.session.get('conversation_history', []),
            predictions=predictions or []
        )
        
        # Save individual question responses
        conversation_history = request.session.get('conversation_history', [])
        order = 0
        
        for i in range(0, len(conversation_history)-1, 2):
            if (i+1 < len(conversation_history) and conversation_history[i]['type'] == 'bot' and 
                conversation_history[i+1]['type'] == 'user'):
                
                question = conversation_history[i]['message']
                answer = conversation_history[i+1]['message']
                
                # Try to extract field name from the question context
                field_name = ''
                if 'current_field' in request.session:
                    field_name = request.session.get('current_field', '')
                
                QuestionResponse.objects.create(
                    quiz_attempt=quiz_attempt,
                    question=question,
                    answer=answer,
                    field_name=field_name,
                    order=order
                )
                order += 1
        return quiz_attempt
        
    except Exception as e:
        print(f"Error saving counseling session: {e}")
        return None
            

@csrf_exempt
@require_POST
def get_conversation_history(request):
    """Get the current conversation history"""
    try:
        history = request.session.get('conversation_history', [])
        return JsonResponse({'history': history})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Add a new view for the counseling interface
def career_counseling(request):
    return render(request, 'career_counseling.html')

# =====================================================
# Get the directory of the current views.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the path to the directory containing the model files
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models2') # Assuming you created an ml_models folder
print(MODEL_DIR)
# Check if model files exist and load them globally for efficiency
# This loads the models only once when Django starts
try:
    with open(os.path.join(MODEL_DIR, "ensemble_models_optuna.pkl"), "rb") as f:
        ENSEMBLE_MODELS = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "rb") as f:
        LABEL_ENCODER = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "scaler.pkl"), "rb") as f:
        SCALER = pickle.load(f)
    print("✅ Career Prediction Models loaded successfully!")
except Exception as e:
    # IMPORTANT: Handle the case where models aren't found or fail to load
    print(f"❌ Error loading ML models: {e}. Check if the files are in {MODEL_DIR}")
    ENSEMBLE_MODELS = None
    LABEL_ENCODER = None
    SCALER = None


# @csrf_exempt
# @require_POST
# def predict_career(request):
#     if not ENSEMBLE_MODELS:
#         return JsonResponse({'error': 'Prediction models are not loaded.'}, status=503)

#     try:
#         data = json.loads(request.body.decode('utf-8'))
        
#         # Define the expected feature keys based on your training script
#         features = [
#             "O_score", "C_score", "E_score", "A_score", "N_score",
#             "Numerical_Aptitude", "Verbal_Aptitude", "Abstract_Reasoning",
#             "Logical_Reasoning","Spatial_Aptitude",
#             "Enjoy_Teamwork", "Creative_Thinking", "Attention_to_Detail"
#         ]
        
#         # Extract features in the correct order
#         input_data = [float(data.get(feat, 0)) for feat in features]
        
#         # 1. Convert to numpy array and reshape for the scaler
#         input_array = np.array(input_data).reshape(1, -1)
        
#         # 2. Scale the input data
#         scaled_input = SCALER.transform(input_array)
        
#         # 3. Ensemble Prediction (Soft Voting)
#         probas_list = [model.predict_proba(scaled_input) for model in ENSEMBLE_MODELS]
#         avg_probas = np.mean(probas_list, axis=0)
        
#         # 4. Get Top 3 Predictions
#         # np.argsort returns indices that would sort the array
#         top3_indices = np.argsort(avg_probas[0])[::-1][:3]
#         top3_careers = LABEL_ENCODER.inverse_transform(top3_indices)
        
#         # 5. Format results with probabilities
#         results = []
#         for career, index in zip(top3_careers, top3_indices):
#             probability = avg_probas[0][index]
#             results.append({
#                 'career': career,
#                 'probability': round(probability * 100, 2) # Percentage
#             })
            
#         return JsonResponse({'predictions': results}, status=200)

#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
#     except KeyError as e:
#         return JsonResponse({'error': f'Missing expected data field: {e}'}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=400)
@csrf_exempt
@require_POST
def predict_career(request):
    if not ENSEMBLE_MODELS:
        return JsonResponse({'error': 'Prediction models are not loaded.'}, status=503)

    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # Use the exact features from training
        features = [
            "O_score", "C_score", "E_score", "A_score", "N_score",
            "Numerical Aptitude", "Spatial Aptitude", "Perceptual Aptitude", 
            "Abstract Reasoning", "Verbal Reasoning",
            "Enjoy_Teamwork", "Creative_Thinking", "Attention_to_Detail"
        ]
        
        # Map collected data to expected features
        feature_mapping = {
            "Numerical Aptitude": "Numerical_Aptitude",
            "Spatial Aptitude": "Spatial_Aptitude",
            "Perceptual Aptitude": None,  # Default value
            "Abstract Reasoning": "Abstract_Reasoning", 
            "Verbal Reasoning": "Verbal_Aptitude"
        }
        
        # Extract features in the correct order with mapping
        input_data = []
        for feat in features:
            if feat in feature_mapping and feature_mapping[feat]:
                mapped_feat = feature_mapping[feat]
                input_data.append(float(data.get(mapped_feat, 5)))
            elif feat in feature_mapping and feature_mapping[feat] is None:
                input_data.append(5.0)  # Default for Perceptual Aptitude
            else:
                input_data.append(float(data.get(feat, 5)))
        
        # Rest of your prediction code remains the same...
        input_array = np.array(input_data).reshape(1, -1)
        scaled_input = SCALER.transform(input_array)
        
        # Ensemble Prediction
        probas_list = [model.predict_proba(scaled_input) for model in ENSEMBLE_MODELS]
        avg_probas = np.mean(probas_list, axis=0)
        
        # Get Top 3 Predictions
        top3_indices = np.argsort(avg_probas[0])[::-1][:3]
        top3_careers = LABEL_ENCODER.inverse_transform(top3_indices)
        
        results = []
        for career, index in zip(top3_careers, top3_indices):
            probability = avg_probas[0][index]
            results.append({
                'career': career,
                'probability': round(probability * 100, 2)
            })
            
        return JsonResponse({'predictions': results}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing expected data field: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=400)

# ====================================================
# 🔹 Existing Views (Unchanged)
# ====================================================



# Temporary in-memory reset tokens (for demo only).
# For production use a DB model or signed tokens with expiry.
reset_tokens = {}

# Gmail credentials (note: don't hardcode credentials in production)
FROM_EMAIL = "soepyaepyaephyoe536@gmail.com"
EMAIL_PASSWORD = "loje ezch hggd lnda"


# -------------------------
# Utility helpers
# -------------------------
def _tr(obj, base: str, language: str = "en") -> str:
    """Return field value for the requested language fallback to _en then base."""
    for field in (f"{base}_{language}", f"{base}_en", base):
        if hasattr(obj, field):
            val = getattr(obj, field) or ""
            if val:
                return val
    return ""


def get_current_language(request):
    #return request.session.get('language', 'en')
    return request.GET.get('lang') or request.session.get('language') or 'en'


# -------------------------
# Authentication / Account
# -------------------------
def login_view(request):
    next_url = request.GET.get('next', '/')
    if request.method == "POST":
        identifier = (request.POST.get("email") or request.POST.get("username") or '').strip()
        password = request.POST.get("password") or ''
        if not identifier or not password:
            messages.error(request, "Please provide both email/username and password.")
            return render(request, 'login.html', {"next": next_url})

        user = None
        try:
            user_obj = User.objects.get(email__iexact=identifier)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            # Redirect to profile if incomplete
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            if not profile.is_complete:
                return redirect(f"{reverse('profile')}?next={next_url or reverse('quiz_hub')}")
            return redirect(next_url or '/')
        else:
            messages.error(request, "Invalid email/username or password.")
            return render(request, 'login.html', {"next": next_url})
    return render(request, 'login.html', {"next": next_url})


def register_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''
        confirm_password = request.POST.get('confirm_password') or ''

        if not username or not password:
            messages.error(request, "Please provide username and password.")
            return redirect('register')
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('register')

        user = User.objects.create_user(username=username, password=password, email=email or "")
        messages.success(request, 'Account created! Now complete your profile for better matches.')
        return redirect(f"{reverse('login')}?next={reverse('profile')}")
    return render(request, 'register.html')


@login_required
def profile(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Only show success popup and redirect if form is valid
            request.session['show_profile_success'] = True
            
            # IMMEDIATE REDIRECT to quiz hub after successful save
            nxt = request.POST.get("next") or request.GET.get("next") or reverse("quiz_hub")
            return redirect(nxt)
        else:
            # Handle form validation errors
            error_messages = []
            
            # Collect field-specific errors
            for field, errors in form.errors.items():
                field_name = field.replace('_', ' ').title()
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        error_messages.append(f"{field_name}: {error}")
            
            # Show all errors
            if error_messages:
                messages.error(request, "❌ Please correct the following errors:")
                for error_msg in error_messages:
                    messages.error(request, f"• {error_msg}")
            else:
                messages.error(request, "⚠️ Please fill in all required fields correctly.")
    else:
        form = StudentProfileForm(instance=profile)

    # Check if we should show the success popup
    show_success_popup = request.session.pop('show_profile_success', False)
    
    return render(request, "profile.html", {
        "form": form, 
        "profile": profile,
        "show_success_popup": show_success_popup
    })





@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('profile')  # Redirect to profile or home page instead
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'changepassword.html', {'form': form})

from django.contrib.auth.forms import PasswordChangeForm
def forgot_password(request):
    if request.method == "POST":
        email = (request.POST.get("email") or '').strip()
        if not email:
            messages.error(request, "Please provide an email address.")
            return render(request, "forgot_password.html")

        try:
            user = User.objects.get(email__iexact=email)
            token = get_random_string(32)
            reset_tokens[token] = user.username  # TEMP store

            reset_link = request.build_absolute_uri(reverse('reset_password', args=[token]))
            subject = "Password Reset Request"
            body = f"""
Hi {user.username},

Click the link below to reset your password:
{reset_link}

If you didn’t request this, you can ignore this email.
"""
            send_email(subject, body, to_email=email, from_email=FROM_EMAIL, password=EMAIL_PASSWORD)
            messages.success(request, "Password reset link sent to your email.")
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")

    return render(request, "forgot_password.html")


def reset_password(request, token):
    if token not in reset_tokens:
        messages.error(request, "Invalid or expired reset link.")
        return redirect('forgot_password')

    if request.method == "POST":
        new_password = request.POST.get("password") or ''
        username = reset_tokens[token]
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        del reset_tokens[token]
        messages.success(request, "Password changed successfully!")
        return redirect('success')

    return render(request, "reset_password.html")


def success(request):
    return render(request, "success.html")


# -----------------------------
# API: Save survey
# ----------------------------
@require_POST
def save_survey(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        category = data.get("category")
        responses = data.get("responses")
        CareerSurvey.objects.create(category=category, responses=responses)
        return JsonResponse({"message": "Survey saved successfully!"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



# -------------------------
# Static pages
# -------------------------
def home(request):
    return render(request, 'k_home.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')

# views.py
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import StudentProfile

@login_required
def quiz_hub(request):
    # Gate: must complete profile first
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if not profile.is_complete:
        messages.info(request, "Build your profile to unlock the quiz. It only takes a minute. 😊")
        return redirect(f"{reverse('profile')}?next={reverse('quiz_hub')}")

    # NEW: pick up the one-time success flag after profile save
    show_success_popup = request.session.pop('show_profile_success', False)

    return render(request, 'quiz_hub.html', {
        'show_success_popup': show_success_popup
    })



def aptitude_test_Q(request):
    return render(request, 'aptitude_test.html')


def educational_test_Q(request):
    return render(request, 'educational_test.html')


def educational_major_selection(request):
    return render(request, 'educational_major_selection.html')


def educational_test_CSE_Q(request):
    return render(request, 'educational_test_CSE.html')


def educational_test_CSE_result(request):
    return render(request, 'educational_test_CSE_result.html')


def combined_test_Q(request):
    return render(request, 'combined_test.html')


def aptitude_test_R(request):
    return render(request, 'aptitude_result.html')


def architecture_path(request):
    language = get_current_language(request)
    return render(request, 'architecture_path.html', {'current_language': language})


def institution_detail(request):
    return render(request, 'institution_detail.html')


def logout_confirm(request):
    return render(request, 'logout.html')

# -----------------------------
# Language switcher (single source of truth)
# -----------------------------
def switch_language(request, language_code):
    if language_code in ["en", "my"]:
        request.session["language"] = language_code
    return redirect(request.META.get("HTTP_REFERER", "/"))


# -----------------------------
# Universities (Public) — language-ready
# -----------------------------
def public_unis(request):
    language = get_current_language(request)
    universities = PublicUniversity.objects.all()

    for uni in universities:
        uni.display_name = _tr(uni, "name", language)
        uni.display_abbreviation = _tr(uni, "abbreviation", language)
        uni.display_location = _tr(uni, "location", language)
        uni.display_description = _tr(uni, "description", language)

    return render(
        request,
        "Universities/PublicUniversities/public_unis.html",
        {"universities": universities, "current_language": language},
    )
    
import random

def public_unis_detail(request, id):
    language = get_current_language(request)
    university = get_object_or_404(PublicUniversity, id=id)
    all_universities = list(PublicUniversity.objects.exclude(id=university.id))
    random_universities = random.sample(all_universities, min(3, len(all_universities)))

    university.display_name = _tr(university, "name", language)
    university.display_abbreviation = _tr(university, "abbreviation", language)
    university.display_location = _tr(university, "location", language)
    university.display_description = _tr(university, "description", language)
    university.display_about = _tr(university, "about", language)
    university.display_highlights = getattr(university, f"highlights_{language}", [])
    
    # For the new fields, check if they exist and have content
    university.display_faculties_departments = _tr(university, "faculties_departments", language)
    # university.display_undergraduate_majors = _tr(university, "undergraduate_majors", language)
    # university.display_graduate_majors = _tr(university, "graduate_majors", language)
    # university.display_doctoral_majors = _tr(university, "doctoral_majors", language)
    university.display_popular_programs = _tr(university, "popular_programs", language)
    university.display_campus_facilities = _tr(university, "campus_facilities", language)
    university.display_student_organizations = _tr(university, "student_organizations", language)
    university.display_international_collaborations = _tr(university, "international_collaborations", language)
    
    # ADD THESE LINES FOR MAJORS:
    university.display_undergraduate_majors = getattr(university, f"undergraduate_majors_{language}", [])
    university.display_graduate_majors = getattr(university, f"graduate_majors_{language}", [])
    university.display_doctoral_majors = getattr(university, f"doctoral_majors_{language}", [])
    
    related_universities = []
    for related_uni in university.related_universities.all():
        # Set display properties for each related university
        related_uni.display_name = _tr(related_uni, "name", language)
        related_uni.display_location = _tr(related_uni, "location", language)
        related_universities.append(related_uni)

    # Get 3 random universities for fallback and set their display properties
    all_universities = list(PublicUniversity.objects.exclude(id=university.id))
    random_universities = random.sample(all_universities, min(3, len(all_universities)))
    
    for random_uni in random_universities:
        random_uni.display_name = _tr(random_uni, "name", language)
        random_uni.display_location = _tr(random_uni, "location", language)


    return render(
        request,
        "Universities/PublicUniversities/public_unis_detail.html",
        {"university": university, "current_language": language, "related_universities": related_universities, "random_universities": random_universities},
    )


# -----------------------------
# Private Colleges — language-ready
# -----------------------------
def private_colls(request):
    language = get_current_language(request)
    colleges = PrivateCollege.objects.all()

    for col in colleges:
        col.display_name = _tr(col, "name", language)
        col.display_abbreviation = _tr(col, "abbreviation", language)
        col.display_location = _tr(col, "location", language)
        col.display_description = _tr(col, "description", language)

    return render(
        request,
        "Universities/PrivateColleges/private_colls.html",
        {"colleges": colleges, "current_language": language},
    )


def private_colls_detail(request, id):
    language = get_current_language(request)
    college = get_object_or_404(PrivateCollege, id=id)
    all_colleges = list(PrivateCollege.objects.exclude(id=college.id))
    random_colleges = random.sample(all_colleges, min(3, len(all_colleges)))

    college.display_name = _tr(college, "name", language)
    college.display_abbreviation = _tr(college, "abbreviation", language)
    college.display_location = _tr(college, "location", language)
    college.display_description = _tr(college, "description", language)
    college.display_about = _tr(college, "about", language)
    college.display_highlights = getattr(college, f"highlights_{language}", [])
    
    # For the new fields, check if they exist and have content
    college.display_faculties_departments = _tr(college, "faculties_departments", language)
    college.display_popular_programs = _tr(college, "popular_programs", language)
    college.display_campus_facilities = _tr(college, "campus_facilities", language)
    college.display_student_organizations = _tr(college, "student_organizations", language)
    college.display_international_collaborations = _tr(college, "international_collaborations", language)
    
    # ADD THESE LINES FOR MAJORS:
    college.display_undergraduate_majors = getattr(college, f"undergraduate_majors_{language}", [])
    college.display_graduate_majors = getattr(college, f"graduate_majors_{language}", [])
    college.display_doctoral_majors = getattr(college, f"doctoral_majors_{language}", [])
    
    related_colleges = []
    for related_colge in college.related_colleges.all():
        # Set display properties for each related college
        related_colge.display_name = _tr(related_colge, "name", language)
        related_colge.display_location = _tr(related_colge, "location", language)
        related_colleges.append(related_colge)

    # Get 3 random universities for fallback and set their display properties
    all_colleges = list(PrivateCollege.objects.exclude(id=college.id))
    random_colleges = random.sample(all_colleges, min(3, len(all_colleges)))
    
    for random_colge in random_colleges:
        random_colge.display_name = _tr(random_colge, "name", language)
        random_colge.display_location = _tr(random_colge, "location", language)

    return render(
        request,
        "Universities/PrivateColleges/private_colls_detail.html",
        {"college": college, "current_language": language,"related_colleges": related_colleges, "random_colleges": random_colleges},
    )


# -----------------------------
# Careers — list / search / detail / by category
# -----------------------------
def career_list(request):
    current_language = request.GET.get('lang') or request.session.get('language') or 'en'
    
    # Store in session for future requests
    request.session['language'] = current_language
    careers = Career.objects.filter(is_active=True).order_by("title_en")

    # A-Z filtering
    letter = request.GET.get("letter", "").upper()
    if letter and len(letter) == 1:
        careers = careers.filter(title_en__istartswith=letter)

    # Category filtering
    category_slug = request.GET.get("category")
    if category_slug:
        careers = careers.filter(category__slug=category_slug)

    # Pagination
    paginator = Paginator(careers, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "selected_letter": letter,
        "selected_category": category_slug,
        "current_language": current_language,
    }
    return render(request, "careers/career_list.html", context)


def career_search(request):
    current_language = get_current_language(request)
    request.session['language'] = current_language
    query = request.GET.get("q", "")

    if query:
        careers = (
            Career.objects.filter(
                Q(title_en__icontains=query)
                | Q(title_my__icontains=query)
                | Q(description_en__icontains=query)
                | Q(description_my__icontains=query)
                | Q(category__name_en__icontains=query)
                | Q(category__name_my__icontains=query)
            )
            .filter(is_active=True)
            .distinct()
        )
    else:
        careers = Career.objects.filter(is_active=True)

    context = {"careers": careers, "query": query, "current_language": current_language}
    return render(request, "careers/career_search.html", context)


def career_detail(request, slug):
    career = get_object_or_404(Career, slug=slug, is_active=True)
    language = get_current_language(request)

    # Related majors (limit 5) and careers (limit 5)
    related_majors = career.get_related_majors()[:5]
    related_careers = (
        Career.objects.filter(category=career.category, is_active=True)
        .exclude(id=career.id)[:5]
    )

    context = {
        "career": career,
        "related_majors": related_majors,
        "related_careers": related_careers,
        "current_language": language,
    }
    return render(request, "careers/career_detail.html", context)


def career_by_category(request, category_slug):
    language = get_current_language(request)
    category = get_object_or_404(Category, slug=category_slug)
    careers = Career.objects.filter(category=category, is_active=True).order_by("title_en")

    context = {"careers": careers, "category": category, "current_language": language}
    return render(request, "careers/career_by_category.html", context)


from django.http import JsonResponse
from django.utils import timezone

def college_last_updated(request, college_id):
    college = get_object_or_404(PrivateCollege, id=college_id)
    return JsonResponse({
        'updated_timestamp': int(college.updated_at.timestamp()),
        'last_updated': college.updated_at.isoformat(),
        'current_time': timezone.now().isoformat()
    })

# In your views.py
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def contact_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Send email
        send_mail(
            f'Career Ladder Contact: {subject}',
            f'Name: {first_name} {last_name}\nEmail: {email}\n\nMessage:\n{message}',
            email,  # from email
            ['https://gmail.com/'],  # to email
            fail_silently=False,
        )
        
        return JsonResponse({'status': 'success'})
def review_page(request):
    # Aggregate review counts by rating
    counts = AppReview.objects.values('rating').annotate(count=Count('rating')).order_by('rating')
    counts_dict = {str(i): 0 for i in range(1, 6)}
    for item in counts:
        counts_dict[str(item['rating'])] = item['count']

    context = {
        'reviews': AppReview.objects.all().order_by('-id'),
        'counts_json': mark_safe(json.dumps(counts_dict)),
    }
    return render(request, 'review_page.html', context)


@login_required
def add_review(request):
    if request.method == 'POST':
        rating = request.POST.get('rating', '')
        text = request.POST.get('text', '').strip()

        # Validate rating
        if not rating.isdigit() or int(rating) not in range(1, 6):
            # Optional: store error in messages or handle better
            return redirect('review_page')

        if not text:
            # Optional: handle this better with messages
            return redirect('review_page')

        # Save review
        AppReview.objects.create(
            name=request.user.username,
            rating=int(rating),
            text=text
        )

        # Redirect to review page after submission
        return redirect('review_page')

    # If someone tries to access this via GET, just redirect
    return redirect('review_page')

# views.py - Add these views

@login_required
def quiz_history(request):
    """Main quiz history page"""
    quiz_attempts = QuizAttempt.objects.filter(user=request.user).select_related('user')
    
    # Group by quiz type for better organization
    quiz_types = {}
    for attempt in quiz_attempts:
        if attempt.quiz_type not in quiz_types:
            quiz_types[attempt.quiz_type] = []
        quiz_types[attempt.quiz_type].append(attempt)
    
    return render(request, 'quiz_history.html', {
        'quiz_types': quiz_types,
        'total_attempts': quiz_attempts.count()
    })

@login_required
def quiz_attempt_detail(request, attempt_id):
    """Detailed view of a specific quiz attempt"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    responses = attempt.responses.all()
    
    return render(request, 'quiz_attempt_detail.html', {
        'attempt': attempt,
        'responses': responses
    })
