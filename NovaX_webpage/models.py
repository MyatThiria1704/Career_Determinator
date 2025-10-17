# models.py
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


# models.py - Add these models

class QuizAttempt(models.Model):
    QUIZ_TYPES = [
        ('AI_COUNSELING', 'AI Career Counseling'),
        ('APTITUDE', 'Aptitude Test'),
        ('PERSONALITY', 'Personality Test'),
        ('EDUCATIONAL', 'Educational Test'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Store the conversation/questions and answers
    conversation_data = models.JSONField(default=dict, blank=True)
    
    # Store predictions/results
    predictions = models.JSONField(default=list, blank=True)
    
    # Overall score if applicable
    score = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_quiz_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class QuestionResponse(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.TextField()
    answer = models.TextField()
    field_name = models.CharField(max_length=100, blank=True)  # e.g., 'C_score', 'O_score'
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
# ===== CAREER MODELS =====
class Category(models.Model):
    name_en = models.CharField(max_length=200)
    name_my = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description_en = models.TextField(blank=True)
    description_my = models.TextField(blank=True)
    university_category_keywords = models.TextField(
        blank=True, help_text="Comma-separated keywords to match with university majors"
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_en

    def get_name(self, language="en"):
        return getattr(self, f"name_{language}", self.name_en)

    def get_related_majors(self):
        if not self.university_category_keywords:
            return Major.objects.none()
        keywords = [
            kw.strip().lower() for kw in self.university_category_keywords.split(",")
        ]
        query = Q()
        for keyword in keywords:
            query |= Q(name_en__icontains=keyword) | Q(
                description_en__icontains=keyword
            )
        return Major.objects.filter(query)


class Career(models.Model):
    title_en = models.CharField(max_length=200)
    title_my = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="careers"
    )
    career_keywords = models.TextField(
        blank=True, help_text="Comma-separated specific keywords"
    )
    description_en = models.TextField()
    description_my = models.TextField(blank=True)
    responsibilities_en = models.TextField()
    skills_required_en = models.TextField()
    education_requirements_en = models.TextField()
    responsibilities_my = models.TextField(blank=True)
    skills_required_my = models.TextField(blank=True)
    education_requirements_my = models.TextField(blank=True)
    salary_range_min = models.DecimalField(max_digits=15, decimal_places=2)
    salary_range_max = models.DecimalField(max_digits=15, decimal_places=2)
    salary_currency = models.CharField(max_length=3, default="USD")
    job_outlook_en = models.CharField(
        max_length=100,
        choices=[
            ("very_high", "Very High Demand"),
            ("high", "High Demand"),
            ("average", "Average Demand"),
            ("low", "Low Demand"),
        ],
    )
    job_outlook_my = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ("entry", "Entry Level"),
            ("mid", "Mid Level"),
            ("senior", "Senior Level"),
            ("executive", "Executive Level"),
        ],
    )
    public_university = models.ForeignKey(
        'PublicUniversity', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        #related_name='careers',
        help_text="Related public university for this career"
    )
    
    private_college = models.ForeignKey(
        'PrivateCollege', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
       # related_name='careers', 
        help_text="Related private college for this career"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title_en

    def get_title(self, language="en"):
        return getattr(self, f"title_{language}", self.title_en)
    
    def get_title_my(self):
        return self.title_my or self.title_en
    
    def get_description(self, language="en"):
        return getattr(self, f"description_{language}", self.description_en)
    
    def get_description_my(self):
        return self.description_my or self.description_en

    def get_related_majors(self, limit=10):
        all_keywords = []
        if self.category.university_category_keywords:
            all_keywords.extend(
                [
                    kw.strip().lower()
                    for kw in self.category.university_category_keywords.split(",")
                ]
            )
        if self.career_keywords:
            all_keywords.extend(
                [kw.strip().lower() for kw in self.career_keywords.split(",")]
            )
        title_words = self.title_en.lower().split()
        all_keywords.extend(title_words)
        all_keywords = list(set(all_keywords))
        if not all_keywords:
            return Major.objects.none()
        query = Q()
        for keyword in all_keywords:
            if len(keyword) > 2:
                query |= Q(name_en__icontains=keyword) | Q(
                    description_en__icontains=keyword
                )
        return Major.objects.filter(query).distinct()[:limit]
    
    def get_public_university_url(self):
        if self.public_university and self.public_university.id:
            from django.urls import reverse
            try:
                return reverse('public_unis_detail', args=(self.public_university.id,))
            except:
                return None
        return None
    
    def get_private_college_url(self):
        if self.private_college and self.private_college.id:
            from django.urls import reverse
            try:
                return reverse('private_colls_detail', args=(self.private_college.id,))
            except:
                return None
        return None

    def get_job_outlook(self, language="en"):
        outlook_map = {
            "very_high": "Very High",
            "high": "High", 
            "average": "Average",
            "low": "Low",
        }
        return outlook_map.get(self.job_outlook_en, "Unknown")
    
    def get_job_outlook_my(self):
        outlook_map = {
            "very_high": "အလွန်မြင့်မားသော",
            "high": "မြင့်မားသော",
            "average": "ပျမ်းမျှ",
            "low": "နိမ့်သော",
        }
        return outlook_map.get(self.job_outlook_en, "မသိရ")


# models.py (add inside Career class)


# def get_description(self, language="en"):
#     # fall back to EN if requested language is empty
#     val = getattr(self, f"description_{language}", None)
#     return val or self.description_en
def get_description(self, language="en"):
        return getattr(self, f"description_{language}", self.description_en)
    
def get_description_my(self):
        return self.description_my or self.description_en


def get_responsibilities(self, language="en"):
    val = getattr(self, f"responsibilities_{language}", None)
    return val or self.responsibilities_en


def get_skills_required(self, language="en"):
    val = getattr(self, f"skills_required_{language}", None)
    return val or self.skills_required_en


def get_education_requirements(self, language="en"):
    val = getattr(self, f"education_requirements_{language}", None)
    return val or self.education_requirements_en


def get_job_outlook(self, language="en"):
    """
    Returns a short, display-friendly label.
    Your EN field stores keys like 'very_high', 'high', etc.
    """
    outlook_map = {
        "very_high": "Very High",
        "high": "High",
        "average": "Average",
        "low": "Low",
    }
    if language == "en":
        return outlook_map.get(self.job_outlook_en, "Unknown")
    # if you later store localized labels in job_outlook_my, use them; else fallback
    return getattr(self, "job_outlook_my", "") or outlook_map.get(
        self.job_outlook_en, "Unknown"
    )

    @property
    def average_salary(self):
        """
        Safe numeric average used by the sidebar card.
        """
        try:
            # Convert to float to handle Decimal fields properly
            min_salary = float(self.salary_range_min)
            max_salary = float(self.salary_range_max)
            return (min_salary + max_salary) / 2
        except (TypeError, ValueError, AttributeError):
            return 0  # Return 0 instead of None


def get_meta_description(self, language="en"):
    """
    Short meta description for the <head>. Adjust to your preference.
    """
    desc = self.get_description(language) or ""
    # take first ~150 chars without breaking words
    snippet = (desc[:147] + "...") if len(desc) > 150 else desc
    return f"{self.get_title(language)} – {snippet}"


# ===== UNIVERSITY MODELS =====
# class PublicUniversity(models.Model):
#     name_en = models.CharField(max_length=200, default="N/A")
#     name_my = models.CharField(max_length=200, blank=True)
#     abbreviation_en = models.CharField(max_length=100, default="N/A")
#     abbreviation_my = models.CharField(max_length=100, blank=True)
#     location_en = models.CharField(max_length=100, default="N/A")
#     location_my = models.CharField(max_length=100, blank=True)
#     established = models.IntegerField()
#     description_en = models.TextField(default="N/A")
#     description_my = models.TextField(blank=True)
#     about_en = models.TextField(default="N/A")
#     about_my = models.TextField(blank=True)
#     website = models.URLField(blank=True, null=True)

#     def __str__(self):
#         return self.name_en

#     def get_name(self, language="en"):
#         return getattr(self, f"name_{language}", self.name_en)


# class PrivateCollege(models.Model):
#     name_en = models.CharField(max_length=200, default="N/A")
#     name_my = models.CharField(max_length=200, blank=True)
#     abbreviation_en = models.CharField(max_length=100, default="N/A")
#     abbreviation_my = models.CharField(max_length=100, blank=True)
#     location_en = models.CharField(max_length=100, default="N/A")
#     location_my = models.CharField(max_length=100, blank=True)
#     established = models.IntegerField()
#     description_en = models.TextField(default="N/A")
#     description_my = models.TextField(blank=True)
#     about_en = models.TextField(default="N/A")
#     about_my = models.TextField(blank=True)
#     website = models.URLField(blank=True, null=True)

#     def __str__(self):
#         return self.name_en

#     def get_name(self, language="en"):
#         return getattr(self, f"name_{language}", self.name_en)

from django.db import models
from django.utils import timezone

class PublicUniversity(models.Model):
    # Existing fields
    name_en = models.CharField(max_length=200, default="N/A")
    name_my = models.CharField(max_length=200, blank=True)
    abbreviation_en = models.CharField(max_length=100, default="N/A")
    abbreviation_my = models.CharField(max_length=100, blank=True)
    location_en = models.CharField(max_length=100, default="N/A")
    location_my = models.CharField(max_length=100, blank=True)
    established = models.IntegerField()
    description_en = models.TextField(default="N/A")
    description_my = models.TextField(blank=True)
    about_en = models.TextField(default="N/A")
    about_my = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    #data_updated_at = models.DateTimeField(null=True, blank=True, help_text="When data was last updated from populate script")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    data_updated_at = models.DateTimeField(null=True, blank=True)
    related_universities = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        help_text="Related universities that students might also be interested in"
    )
    total_students = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Total number of students (e.g., '15,000+', '20,000')"
    )
    faculty_members = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Number of faculty members (e.g., '800+', '1,200')"
    )
    total_programs = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Number of programs offered (e.g., '50+', '75')"
    )
    highlights_en = models.JSONField(
        default=list,
        help_text="Key highlights in English as JSON list of objects with 'title' and 'description'"
    )
    highlights_my = models.JSONField(
        default=list,
        help_text="Key highlights in Myanmar as JSON list of objects with 'title' and 'description'"
    )
    
    @property
    def last_updated(self):
        # Prefer data_updated_at, fall back to updated_at
        return self.data_updated_at or self.updated_at
    
    @property
    def last_updated_timestamp(self):
        """Return timestamp for JavaScript"""
        last_update = self.last_updated
        return int(last_update.timestamp()) if last_update else None

    def mark_data_updated(self):
        """Call this when data is updated from populate script"""
        self.data_updated_at = timezone.now()
        self.save(update_fields=['data_updated_at', 'updated_at'])
        
    def get_highlights(self, language="en"):
        """Get highlights for the specified language"""
        return getattr(self, f"highlights_{language}", [])
    
    # New fields for Faculties/Departments
    faculties_departments_en = models.TextField(
        default=list, 
        help_text="List of faculties/departments in English"
    )
    faculties_departments_my = models.TextField(
        default=list, 
        help_text="List of faculties/departments in Myanmar"
    )
    
    # Enhanced fields for Programs/Majors by degree level
    undergraduate_majors_en = models.JSONField(
        default=list,
        help_text="Undergraduate majors in English"
    )
    undergraduate_majors_my = models.JSONField(
        default=list,
        help_text="Undergraduate majors in Myanmar"
    )
    
    graduate_majors_en = models.JSONField(
        default=list,
        help_text="Graduate majors in English"
    )
    graduate_majors_my = models.JSONField(
        default=list,
        help_text="Graduate majors in Myanmar"
    )
    
    doctoral_majors_en = models.JSONField(
        default=list,
        help_text="Doctoral majors in English"
    )
    doctoral_majors_my = models.JSONField(
        default=list,
        help_text="Doctoral majors in Myanmar"
    )
    
    # New fields for Popular programs or majors
    popular_programs_en = models.TextField(
        default=list, 
        help_text="Popular programs or majors in English"
    )
    popular_programs_my = models.TextField(
        default=list, 
        help_text="Popular programs or majors in Myanmar"
    )
    
    # New fields for Degree types offered
    degree_types_offered = models.JSONField(
        default=list, 
        help_text="List of degree types offered (Bachelor, Master, PhD, etc.)"
    )
    
    # New fields for Campus facilities
    campus_facilities_en = models.TextField(
        default=list, 
        help_text="Campus facilities in English (libraries, labs, sports, dorms)"
    )
    campus_facilities_my = models.TextField(
        default=list, 
        help_text="Campus facilities in Myanmar"
    )
    
    # New fields for Student organizations/clubs/societies
    student_organizations_en = models.TextField(
        default=list, 
        help_text="Student organizations/clubs/societies in English"
    )
    student_organizations_my = models.TextField(
        default=list, 
        help_text="Student organizations/clubs/societies in Myanmar"
    )
    
    # New fields for International collaborations or exchange programs
    international_collaborations_en = models.TextField(
        default=list, 
        help_text="International collaborations or exchange programs in English"
    )
    international_collaborations_my = models.TextField(
        default=list, 
        help_text="International collaborations or exchange programs in Myanmar"
    )
    
    # New fields for Rankings
    national_ranking = models.CharField(max_length=100, null=True, blank=True)

    international_ranking = models.CharField(max_length=100, null=True, blank=True)

    
    # New field for Campus map
    campus_map_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL to campus map"
    )

    def __str__(self):
        return self.name_en

    def get_name(self, language="en"):
        return getattr(self, f"name_{language}", self.name_en)
    
    def get_undergraduate_majors(self, language="en"):
        """Get undergraduate majors for the specified language"""
        return getattr(self, f"undergraduate_majors_{language}", [])
    
    def get_graduate_majors(self, language="en"):
        """Get graduate majors for the specified language"""
        return getattr(self, f"graduate_majors_{language}", [])
    
    def get_doctoral_majors(self, language="en"):
        """Get doctoral majors for the specified language"""
        return getattr(self, f"doctoral_majors_{language}", [])
    
    def has_undergraduate_programs(self):
        """Check if university offers undergraduate programs"""
        return bool(self.undergraduate_majors_en or self.undergraduate_majors_my)
    
    def has_graduate_programs(self):
        """Check if university offers graduate programs"""
        return bool(self.graduate_majors_en or self.graduate_majors_my)
    
    def has_doctoral_programs(self):
        """Check if university offers doctoral programs"""
        return bool(self.doctoral_majors_en or self.doctoral_majors_my)



class PrivateCollege(models.Model):
    # Existing fields
    name_en = models.CharField(max_length=200, default="N/A")
    name_my = models.CharField(max_length=200, blank=True)
    abbreviation_en = models.CharField(max_length=100, default="N/A")
    abbreviation_my = models.CharField(max_length=100, blank=True)
    location_en = models.CharField(max_length=100, default="N/A")
    location_my = models.CharField(max_length=100, blank=True)
    established = models.IntegerField()
    description_en = models.TextField(default="N/A")
    description_my = models.TextField(blank=True)
    about_en = models.TextField(default="N/A")
    about_my = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    data_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    related_colleges = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        help_text="Related colleges that students might also be interested in"
    )
    total_students = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Total number of students (e.g., '5,000+', '8,000')"
    )
    faculty_members = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Number of faculty members (e.g., '200+', '350')"
    )
    total_programs = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Number of programs offered (e.g., '30+', '45')"
    )
    highlights_en = models.JSONField(
        default=list,
        help_text="Key highlights in English as JSON list of objects with 'title' and 'description'"
    )
    highlights_my = models.JSONField(
        default=list,
        help_text="Key highlights in Myanmar as JSON list of objects with 'title' and 'description'"
    )
    
    @property
    def last_updated(self):
        # Prefer data_updated_at, fall back to updated_at
        return self.data_updated_at or self.updated_at
    
    @property
    def last_updated_timestamp(self):
        """Return timestamp for JavaScript"""
        last_update = self.last_updated
        return int(last_update.timestamp()) if last_update else None

    def mark_data_updated(self):
        """Call this when data is updated from populate script"""
        self.data_updated_at = timezone.now()
        self.save(update_fields=['data_updated_at', 'updated_at'])
    
    def get_highlights(self, language="en"):
        """Get highlights for the specified language"""
        return getattr(self, f"highlights_{language}", [])
    
    # New fields for Faculties/Departments
    faculties_departments_en = models.TextField(
        default=list, 
        help_text="List of faculties/departments in English"
    )
    faculties_departments_my = models.TextField(
        default=list, 
        help_text="List of faculties/departments in Myanmar"
    )
    
    # Enhanced fields for Programs/Majors by degree level
    undergraduate_majors_en = models.JSONField(
        default=list,
        help_text="Undergraduate majors in English"
    )
    undergraduate_majors_my = models.JSONField(
        default=list,
        help_text="Undergraduate majors in Myanmar"
    )
    
    graduate_majors_en = models.JSONField(
        default=list,
        help_text="Graduate majors in English"
    )
    graduate_majors_my = models.JSONField(
        default=list,
        help_text="Graduate majors in Myanmar"
    )
    
    doctoral_majors_en = models.JSONField(
        default=list,
        help_text="Doctoral majors in English"
    )
    doctoral_majors_my = models.JSONField(
        default=list,
        help_text="Doctoral majors in Myanmar"
    )
    
    # New fields for Popular programs or majors
    popular_programs_en = models.TextField(
        default=list, 
        help_text="Popular programs or majors in English"
    )
    popular_programs_my = models.TextField(
        default=list, 
        help_text="Popular programs or majors in Myanmar"
    )
    
    # New fields for Degree types offered
    degree_types_offered = models.JSONField(
        default=list, 
        help_text="List of degree types offered (Bachelor, Master, PhD, etc.)"
    )
    
    # New fields for Campus facilities
    campus_facilities_en = models.TextField(
        default=list, 
        help_text="Campus facilities in English (libraries, labs, sports, dorms)"
    )
    campus_facilities_my = models.TextField(
        default=list, 
        help_text="Campus facilities in Myanmar"
    )
    
    # New fields for Student organizations/clubs/societies
    student_organizations_en = models.TextField(
        default=list, 
        help_text="Student organizations/clubs/societies in English"
    )
    student_organizations_my = models.TextField(
        default=list, 
        help_text="Student organizations/clubs/societies in Myanmar"
    )
    
    # New fields for International collaborations or exchange programs
    international_collaborations_en = models.TextField(
        default=list, 
        help_text="International collaborations or exchange programs in English"
    )
    international_collaborations_my = models.TextField(
        default=list, 
        help_text="International collaborations or exchange programs in Myanmar"
    )
    
    # New fields for Rankings
    national_ranking = models.CharField(max_length=100, null=True, blank=True)

    international_ranking = models.CharField(max_length=100, null=True, blank=True)

    
    # New field for Campus map
    campus_map_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL to campus map"
    )

    def __str__(self):
        return self.name_en

    def get_name(self, language="en"):
        return getattr(self, f"name_{language}", self.name_en)
    
    def get_undergraduate_majors(self, language="en"):
        """Get undergraduate majors for the specified language"""
        return getattr(self, f"undergraduate_majors_{language}", [])
    
    def get_graduate_majors(self, language="en"):
        """Get graduate majors for the specified language"""
        return getattr(self, f"graduate_majors_{language}", [])
    
    def get_doctoral_majors(self, language="en"):
        """Get doctoral majors for the specified language"""
        return getattr(self, f"doctoral_majors_{language}", [])
    
    def has_undergraduate_programs(self):
        """Check if university offers undergraduate programs"""
        return bool(self.undergraduate_majors_en or self.undergraduate_majors_my)
    
    def has_graduate_programs(self):
        """Check if university offers graduate programs"""
        return bool(self.graduate_majors_en or self.graduate_majors_my)
    
    def has_doctoral_programs(self):
        """Check if university offers doctoral programs"""
        return bool(self.doctoral_majors_en or self.doctoral_majors_my)


class Major(models.Model):
    name_en = models.CharField(max_length=200)
    name_my = models.CharField(max_length=200, blank=True)
    description_en = models.TextField()
    description_my = models.TextField(blank=True)
    category_en = models.CharField(max_length=200)
    category_my = models.CharField(max_length=200, blank=True)
    duration = models.CharField(max_length=50)
    degree_type = models.CharField(
        max_length=100,
        choices=[
            ("bachelor", "Bachelor Degree"),
            ("master", "Master Degree"),
            ("phd", "PhD"),
            ("diploma", "Diploma"),
            ("certificate", "Certificate"),
        ],
    )
    public_university = models.ForeignKey(
        PublicUniversity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="majors",
    )
    private_college = models.ForeignKey(
        PrivateCollege,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="majors",
    )
    career_opportunities_en = models.TextField(blank=True)
    career_opportunities_my = models.TextField(blank=True)
    admission_requirements_en = models.TextField(blank=True)
    admission_requirements_my = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name_en} - {self.get_university_name()}"

    def get_name(self, language="en"):
        return getattr(self, f"name_{language}", self.name_en)

    def get_university_name(self, language="en"):
        if self.public_university:
            return self.public_university.get_name(language)
        elif self.private_college:
            return self.private_college.get_name(language)
        return "Unknown University"

    def get_university_website(self):
        """Get university website URL"""
        if self.public_university and self.public_university.website:
            return self.public_university.website
        elif self.private_college and self.private_college.website:
            return self.private_college.website
        return None


# ===== QUIZ/SURVEY MODELS =====
class CareerSurvey(models.Model):
    category = models.CharField(max_length=200)
    responses = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# models.py (add inside Career class)


def get_description(self, language="en"):
    # fall back to EN if requested language is empty
    val = getattr(self, f"description_{language}", None)
    return val or self.description_en


def get_responsibilities(self, language="en"):
    val = getattr(self, f"responsibilities_{language}", None)
    return val or self.responsibilities_en


def get_skills_required(self, language="en"):
    val = getattr(self, f"skills_required_{language}", None)
    return val or self.skills_required_en


def get_education_requirements(self, language="en"):
    val = getattr(self, f"education_requirements_{language}", None)
    return val or self.education_requirements_en


def get_job_outlook(self, language="en"):
    """
    Returns a short, display-friendly label.
    Your EN field stores keys like 'very_high', 'high', etc.
    """
    outlook_map = {
        "very_high": "Very High",
        "high": "High",
        "average": "Average",
        "low": "Low",
    }
    if language == "en":
        return outlook_map.get(self.job_outlook_en, "Unknown")
    # if you later store localized labels in job_outlook_my, use them; else fallback
    return getattr(self, "job_outlook_my", "") or outlook_map.get(
        self.job_outlook_en, "Unknown"
    )


@property
def average_salary(self):
    """
    Safe numeric average calculation
    """
    try:
        # Check if both values exist
        if self.salary_range_min is None or self.salary_range_max is None:
            return 0

        # Convert to float to handle Decimal fields
        min_val = float(self.salary_range_min)
        max_val = float(self.salary_range_max)

        # Calculate average
        average = (min_val + max_val) / 2

        # Return rounded value
        return round(average, 2)

    except (TypeError, ValueError, AttributeError) as e:
        print(f"Error calculating average salary: {e}")
        return 0

def get_meta_description(self, language="en"):
    """
    Short meta description for the <head>. Adjust to your preference.
    """
    desc = self.get_description(language) or ""
    # take first ~150 chars without breaking words
    snippet = (desc[:147] + "...") if len(desc) > 150 else desc
    return f"{self.get_title(language)} – {snippet}"


from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class StudentProfile(models.Model):
    EXAM_CHOICES = [
        ("none", "Not taken"),
        ("matriculation", "Matriculation Exam"),
        ("igcse", "IGCSE"),
        ("ged", "GED"),
    ]
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150, blank=True)  # display name
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(10), MaxValueValidator(100)])
    phone = models.CharField(max_length=20, null=True, blank=True)

    # Exam info
    exam_type = models.CharField(max_length=20, choices=EXAM_CHOICES, default="none")
    passed_date = models.DateField(null=True, blank=True)  # matric/igcse/ged passed date (if applicable)
    passed_school = models.CharField(max_length=120, blank=True)  # e.g. "MA HLAING", "CAE"

    # Subject marks – flexible per-track
    subject_marks = models.JSONField(default=dict, blank=True)
    # example structure:
    # {
    #   "matriculation": {"Myanmar": 80, "English": 77, "Maths": 85, ...},
    #   "igcse": {"Math": "A", "English": "B", ...},
    #   "ged": {"Math": 165, "RLA": 160, ...}
    # }

    # History test taken – lightweight audit (kept separate from QuizAttempt table)
    history_tests_taken = models.JSONField(default=list, blank=True)
    # e.g. ["Aptitude 2025-09-01", "Educational CSE 2025-09-16"]

    # Misc (you already reference this from the header)
    photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)

    # Optional legacy fields (keep if you still use them elsewhere)
    last_school = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def is_complete(self):
        """
        Minimal criteria to allow quiz access.
        Tweak as you like.
        """
        basic_ok = bool(self.full_name and self.gender and self.age and self.phone)
        if self.exam_type == "none":
            return basic_ok
        # If exam taken, also require school and passed_date
        return basic_ok and bool(self.passed_school and self.passed_date)
class AppReview(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.rating}★)"