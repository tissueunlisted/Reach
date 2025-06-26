# C:\entc\core_app\urls.py

from django.urls import path
from . import views # Import views from the current app
from django.contrib.auth import views as auth_views
from .forms import SignUpForm

urlpatterns = [
    # General pages
    path('', views.home, name='home'),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', views.signup, name='signup'),

    # Class Management URLs
    path('classes/create/', views.create_class, name='create_class'),
    path('classes/join/', views.join_class, name='join_class'),

    # Quiz Management URLs
    path('quizzes/create/', views.create_quiz, name='create_quiz'),
    path('quizzes/edit/<int:quiz_id>/', views.create_quiz, name='edit_quiz'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/take/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quizzes/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('quizzes/dashboard/<int:quiz_id>/', views.teacher_quiz_dashboard, name='teacher_quiz_dashboard'),

    # Flashcard Management URLs (Teacher)
    path('flashcards/create/', views.create_flashcard_set, name='create_flashcard_set'),
    path('flashcards/edit/<int:flashcard_set_id>/', views.create_flashcard_set, name='edit_flashcard_set'),
    
    # Flashcard Study URLs (Student)
    path('flashcards/', views.flashcard_set_list, name='flashcard_set_list'),
    path('flashcards/study/<int:flashcard_set_id>/', views.study_flashcard_set, name='study_flashcard_set'),

    # Leaderboard URL
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # Lecture Note URLs (CRITICAL: Ensure these exist and are correctly named)
    path('notes/create/', views.create_lecture_note, name='create_lecture_note'), # This one!
    path('notes/edit/<int:note_id>/', views.create_lecture_note, name='edit_lecture_note'),
    path('notes/', views.lecture_note_list, name='lecture_note_list'),
    path('notes/<int:note_id>/', views.view_lecture_note, name='view_lecture_note'),
]
