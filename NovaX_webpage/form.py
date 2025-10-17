from django import forms
from .models import StudentProfile
import json
from .models import AppReview

class StudentProfileForm(forms.ModelForm):
    subject_marks_json = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = StudentProfile
        fields = [
            "full_name", "gender", "age", "phone", "photo",
            "exam_type", "passed_date", "passed_school",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "min": "10", "max": "100"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "09…"}),
            "exam_type": forms.Select(attrs={"class": "form-select"}),
            "passed_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "passed_school": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., MA HLAING, CAE"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Check basic required fields
        required_fields = {
            'full_name': 'Full Name',
            'gender': 'Gender', 
            'age': 'Age',
            'phone': 'Phone Number',
            'exam_type': 'Exam Type'
        }
        
        missing_fields = []
        for field, display_name in required_fields.items():
            value = cleaned_data.get(field)
            if not value:
                missing_fields.append(display_name)
        
        if missing_fields:
            raise forms.ValidationError(
                f"Please fill in the following required fields: {', '.join(missing_fields)}"
            )

        # Validate exam-specific requirements
        exam_type = cleaned_data.get('exam_type')
        
        if exam_type and exam_type != 'none':
            # If exam is taken, require passed_date and passed_school
            if not cleaned_data.get('passed_date'):
                raise forms.ValidationError("Passed date is required when an exam type is selected.")
            
            if not cleaned_data.get('passed_school'):
                raise forms.ValidationError("School name is required when an exam type is selected.")
            
            # Validate subject marks JSON for taken exams
            raw_marks = self.data.get("subject_marks_json", "{}")  # Default to empty JSON object
            try:
                parsed = json.loads(raw_marks)
                if not isinstance(parsed, dict):
                    raise forms.ValidationError("Invalid marks format. Please check your subject entries.")
                
                # Check if we have at least FOUR subjects with marks
                valid_entries = 0
                for subject, mark in parsed.items():
                    if subject and subject.strip() and mark and mark.strip():
                        valid_entries += 1  # Fixed: increment by 1, not 4
                
                if valid_entries < 4:  # Changed to require at least 4 subjects
                    raise forms.ValidationError("Please add at least four subjects with marks for the selected exam.")
                
                self.cleaned_data["parsed_subject_marks"] = parsed
                    
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid marks data format. Please add at least four subjects with marks.")
            except ValueError as e:
                raise forms.ValidationError(str(e))
        else:
            # For "none" exam type, still process marks if provided but don't require
            raw_marks = self.data.get("subject_marks_json", "{}")
            try:
                parsed = json.loads(raw_marks) if raw_marks else {}
                if isinstance(parsed, dict):
                    self.cleaned_data["parsed_subject_marks"] = parsed
            except:
                pass  # Ignore JSON errors for "none" exam type

        return cleaned_data

    def save(self, commit=True):
        inst = super().save(commit=False)
        
        # Save subject marks if available
        exam_type = self.cleaned_data.get("exam_type")
        parsed_marks = self.cleaned_data.get("parsed_subject_marks", {})
        
        if exam_type and exam_type != "none" and parsed_marks:
            existing = inst.subject_marks or {}
            existing[exam_type] = parsed_marks
            inst.subject_marks = existing
        
        if commit:
            inst.save()
        
        return inst
class AppReviewForm(forms.ModelForm):
    class Meta:
        model = AppReview
        fields = ['name', 'rating', 'text']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your review...'}),
            'rating': forms.HiddenInput(),  
        }