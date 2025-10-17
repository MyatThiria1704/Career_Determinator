from django.urls import path
from . import views
from django.contrib.auth import views as auth_views 
from .views import login_view

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('quiz_hub/', views.quiz_hub, name='quiz_hub'),
    
    path('aptitude_test/', views.aptitude_test_Q, name='aptitude_test_Q'),
    path('aptitude_result/', views.aptitude_test_R, name='aptitude_test_R'),
    path('educational_test/', views.educational_test_Q, name='educational_test_Q'),
    path('educational_major_selection/', views.educational_major_selection, name='educational_major_selection'),
    path('educational_major_selection/educational_test_CSE/', views.educational_test_CSE_Q, name='educational_test_CSE_Q'),
    path('educational_test_CSE_result/', views.educational_test_CSE_result, name='educational_test_CSE_result'),
    path('combined_test/', views.combined_test_Q, name='combined_test_Q'),
    path('api/save-survey/', views.save_survey, name='save_survey'),
    
      
    path('architecture_path/', views.architecture_path, name='architecture_path'),
    path('institution_detail/', views.institution_detail, name='institution_detail'),
    
    path('private_colls/', views.private_colls, name='private_colls'),
    path('private_colls/<int:id>/', views.private_colls_detail, name='private_colls_detail'),
    
    path('public_unis/', views.public_unis, name='public_unis'),
    path('public_unis/<int:id>/', views.public_unis_detail, name='public_unis_detail'),

    
    path('register/', views.register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout-confirm/', views.logout_confirm, name='logout_confirm'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset/<str:token>/', views.reset_password, name='reset_password'),
    path('success/', views.success, name='success'),
    path('profile/', views.profile, name='profile'),
    path('changepassword/', views.change_password, name='changepassword'),
    path('reviews/', views.review_page, name='review_page'),  
    path('reviews/add/', views.add_review, name='add_review'),
    # Career URLs
    path('careers/', views.career_list, name='career_list'),
    path('careers/search/', views.career_search, name='career_search'),
    path('careers/<slug:slug>/', views.career_detail, name='career_detail'),
    
    # Language switching
    path('switch-language/<str:language_code>/', views.switch_language, name='switch_language'),
    
    path('api/college/<int:college_id>/last-updated/', views.college_last_updated, name='college_last_updated'),
    # AI Counseling URLs
    path('predict-career/', views.predict_career, name='predict_career'),
    path('career-counseling/', views.career_counseling, name='career_counseling'),
    path('start-counseling/', views.start_counseling, name='start_counseling'),
    path('process-answer/', views.process_counseling_answer, name='process_answer'),
    path('download-report/', views.download_career_report, name='download_report'),
    path('conversation-history/', views.get_conversation_history, name='conversation_history'),

    path('profile/quiz-history/', views.quiz_history, name='quiz_history'),
    path('profile/quiz-history/<int:attempt_id>/', views.quiz_attempt_detail, name='quiz_attempt_detail'),
]
