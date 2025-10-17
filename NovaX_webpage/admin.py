# admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Career, PublicUniversity, PrivateCollege, Major, CareerSurvey

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_my', 'slug', 'get_major_count']
    prepopulated_fields = {'slug': ('name_en',)}
    search_fields = ['name_en', 'name_my']
    
    def get_major_count(self, obj):
        return obj.get_related_majors().count()
    get_major_count.short_description = 'Related Majors'

@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'category', 'salary_range_min', 'salary_range_max', 'get_related_majors_count', 'is_active']
    list_filter = ['category', 'job_outlook_en', 'experience_level', 'is_active']
    prepopulated_fields = {'slug': ('title_en',)}
    search_fields = ['title_en', 'title_my', 'description_en']
    readonly_fields = ['created_at', 'updated_at', 'get_related_majors_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title_en', 'title_my', 'slug', 'category', 'career_keywords', 'is_active')
        }),
        ('English Content', {
            'fields': ('description_en', 'responsibilities_en', 'skills_required_en', 'education_requirements_en')
        }),
        ('Myanmar Content', {
            'fields': ('description_my', 'responsibilities_my', 'skills_required_my', 'education_requirements_my')
        }),
        ('Salary Information', {
            'fields': ('salary_range_min', 'salary_range_max', 'salary_currency')
        }),
        ('Job Market', {
            'fields': ('job_outlook_en', 'job_outlook_my', 'experience_level')
        }),
        ('Auto-Related Majors Preview', {
            'fields': ('get_related_majors_preview',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_related_majors_count(self, obj):
        return obj.get_related_majors().count()
    get_related_majors_count.short_description = 'Auto Majors'
    
    def get_related_majors_preview(self, obj):
        majors = obj.get_related_majors()[:5]
        if majors:
            html = '<ul>'
            for major in majors:
                html += f'<li>{major.name_en} - {major.get_university_name()}</li>'
            html += '</ul>'
            if obj.get_related_majors().count() > 5:
                html += f'<p>... and {obj.get_related_majors().count() - 5} more</p>'
            return mark_safe(html)
        return "No related majors found. Add keywords to category or career."

# @admin.register(PublicUniversity)
# class PublicUniversityAdmin(admin.ModelAdmin):
#     list_display = ['name_en', 'name_my', 'abbreviation_en', 'location_en', 'established']
#     search_fields = ['name_en', 'name_my', 'location_en']
#     list_filter = ['location_en', 'established']
#     ordering = ('name_en',)

#     fieldsets = (
#         ('Basic Information (English)', {
#             'fields': ('name_en', 'abbreviation_en', 'location_en', 'established', 'website')
#         }),
#         ('Basic Information (Myanmar)', {
#             'fields': ('name_my', 'abbreviation_my', 'location_my')
#         }),
#         ('Content (English)', {
#             'fields': ('description_en', 'about_en')
#         }),
#         ('Content (Myanmar)', {
#             'fields': ('description_my', 'about_my')
#         }),
#     )

# @admin.register(PrivateCollege)
# class PrivateCollegeAdmin(admin.ModelAdmin):
#     list_display = ['name_en', 'name_my', 'abbreviation_en', 'location_en', 'established']
#     search_fields = ['name_en', 'name_my', 'location_en']
#     list_filter = ['location_en', 'established']
#     ordering = ('name_en',)

#     fieldsets = (
#         ('Basic Information (English)', {
#             'fields': ('name_en', 'abbreviation_en', 'location_en', 'established', 'website')
#         }),
#         ('Basic Information (Myanmar)', {
#             'fields': ('name_my', 'abbreviation_my', 'location_my')
#         }),
#         ('Content (English)', {
#             'fields': ('description_en', 'about_en')
#         }),
#         ('Content (Myanmar)', {
#             'fields': ('description_my', 'about_my')
#         }),
#     )

from django.contrib import admin
from .models import PublicUniversity, PrivateCollege

@admin.register(PublicUniversity)
class PublicUniversityAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_my', 'abbreviation_en', 'location_en', 'established', 'national_ranking']
    search_fields = ['name_en', 'name_my', 'location_en', 'abbreviation_en']
    list_filter = ['location_en', 'established', 'national_ranking']
    ordering = ('name_en',)

    fieldsets = (
        ('Basic Information (English)', {
            'fields': ('name_en', 'abbreviation_en', 'location_en', 'established', 'website')
        }),
        ('Basic Information (Myanmar)', {
            'fields': ('name_my', 'abbreviation_my', 'location_my')
        }),
        ('Content (English)', {
            'fields': ('description_en', 'about_en')
        }),
        ('Content (Myanmar)', {
            'fields': ('description_my', 'about_my')
        }),
        ('Faculties & Departments', {
            'fields': ('faculties_departments_en', 'faculties_departments_my')
        }),
         ('Programs & Majors - Undergraduate', {
            'fields': ('undergraduate_majors_en', 'undergraduate_majors_my')
        }),
        ('Programs & Majors - Graduate', {
            'fields': ('graduate_majors_en', 'graduate_majors_my')
        }),
        ('Programs & Majors - Doctoral', {
            'fields': ('doctoral_majors_en', 'doctoral_majors_my')
        }),
        ('Popular Programs', {
            'fields': ('popular_programs_en', 'popular_programs_my', 'degree_types_offered')
        }),
        ('Campus Facilities', {
            'fields': ('campus_facilities_en', 'campus_facilities_my')
        }),
        ('Student Life', {
            'fields': ('student_organizations_en', 'student_organizations_my')
        }),
        ('International Relations', {
            'fields': ('international_collaborations_en', 'international_collaborations_my')
        }),
        ('Rankings & Maps', {
            'fields': ('national_ranking', 'international_ranking', 'campus_map_url')
        }),
        ('Statistics', {
            'fields': ('total_students', 'faculty_members', 'total_programs')
        }),
    )

@admin.register(PrivateCollege)
class PrivateCollegeAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_my', 'abbreviation_en', 'location_en', 'established', 'national_ranking']
    search_fields = ['name_en', 'name_my', 'location_en', 'abbreviation_en']
    list_filter = ['location_en', 'established', 'national_ranking']
    ordering = ('name_en',)

    fieldsets = (
        ('Basic Information (English)', {
            'fields': ('name_en', 'abbreviation_en', 'location_en', 'established', 'website')
        }),
        ('Basic Information (Myanmar)', {
            'fields': ('name_my', 'abbreviation_my', 'location_my')
        }),
        ('Content (English)', {
            'fields': ('description_en', 'about_en')
        }),
        ('Content (Myanmar)', {
            'fields': ('description_my', 'about_my')
        }),
        ('Faculties & Departments', {
            'fields': ('faculties_departments_en', 'faculties_departments_my')
        }),
         ('Programs & Majors - Undergraduate', {
            'fields': ('undergraduate_majors_en', 'undergraduate_majors_my')
        }),
        ('Programs & Majors - Graduate', {
            'fields': ('graduate_majors_en', 'graduate_majors_my')
        }),
        ('Programs & Majors - Doctoral', {
            'fields': ('doctoral_majors_en', 'doctoral_majors_my')
        }),
        ('Popular Programs', {
            'fields': ('popular_programs_en', 'popular_programs_my', 'degree_types_offered')
        }),
        ('Campus Facilities', {
            'fields': ('campus_facilities_en', 'campus_facilities_my')
        }),
        ('Student Life', {
            'fields': ('student_organizations_en', 'student_organizations_my')
        }),
        ('International Relations', {
            'fields': ('international_collaborations_en', 'international_collaborations_my')
        }),
        ('Rankings & Maps', {
            'fields': ('national_ranking', 'international_ranking', 'campus_map_url')
        }),
        ('Statistics', {
            'fields': ('total_students', 'faculty_members', 'total_programs')
        }),
    )

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_my', 'get_university_name', 'degree_type', 'duration']
    list_filter = ['degree_type', 'public_university', 'private_college']
    search_fields = ['name_en', 'name_my', 'description_en']
    
    def get_university_name(self, obj):
        return obj.get_university_name()
    get_university_name.short_description = 'University'

@admin.register(CareerSurvey)
class CareerSurveyAdmin(admin.ModelAdmin):
    list_display = ['category', 'created_at']
    list_filter = ['category', 'created_at']
    readonly_fields = ['created_at']

# admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "gender", "age", "exam_type", "passed_school", "passed_date")
    list_filter  = ("exam_type", "gender")
    search_fields = ("user__username", "user__email", "full_name", "phone", "passed_school")
    readonly_fields = ()  # add "subject_marks" here if you want it read-only
    fieldsets = (
        (None, {
            "fields": (
                "user",
                "photo",
                "full_name", "gender", "age", "phone",
                "exam_type", "passed_date", "passed_school",
                "subject_marks", "history_tests_taken",
            )
        }),
    )




# Optional: show Profile inline on the built-in User page
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    fk_name = "user"
    extra = 0

class UserAdmin(BaseUserAdmin):
    inlines = (StudentProfileInline,)
    list_display = BaseUserAdmin.list_display + ("email",)

# Unregister the original User admin, then register our extended one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
