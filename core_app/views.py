# C:\entc\core_app\views.py

import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.forms import inlineformset_factory
from .forms import (
    SignUpForm,
    ClassCreationForm,
    ClassJoinForm,
    QuizForm,
    QuestionFormSet,
    AnswerForm,
    FlashcardSetForm,
    FlashcardFormSet,
    LectureNoteForm
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.forms import formset_factory 
from .models import (
    Class,
    Quiz,
    Question,
    Answer,
    UserProfile,
    FlashcardSet,
    Flashcard,
    FlashcardEngagement,
    QuizAttempt,
    AnswerChoice,
    LectureNote
)
from django.db.models import Q, Avg, Count
import markdown


# Test functions for user types (for user_passes_test decorator)
def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.user_type == 'teacher'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.user_type == 'student'


def home(request):
    """
    Renders the homepage.
    Displays different content based on whether the user is logged in
    and their user type.
    """
    # DEBUG LINE: Check authentication status
    print(f"DEBUG: User authenticated status in home view: {request.user.is_authenticated}")
    print(f"DEBUG: User object: {request.user}")
    
    context = {}
    if request.user.is_authenticated:
        # Crucial check: Ensure the user has a profile.
        # This block might create a profile if it doesn't exist, which can happen if
        # a user logs in but their profile wasn't created by a signal (e.g., if signals were off during initial user creation).
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            # Attempt to create a profile, defaulting to 'student'
            try:
                UserProfile.objects.create(user=request.user, user_type='student')
                messages.info(request, "Your user profile was initialized. Please refresh if needed.")
            except Exception as e:
                # Log any errors if profile creation fails for some reason
                print(f"DEBUG: Error creating UserProfile for {request.user.username}: {e}")
                messages.error(request, f"Error initializing user profile: {e}. Please contact support.")

        # Re-check profile after potential creation
        if hasattr(request.user, 'profile') and request.user.profile is not None:
            if request.user.profile.user_type == 'teacher':
                # For teachers: Show classes they teach, quizzes they created, flashcard sets, and lecture notes
                teacher_classes = Class.objects.filter(teacher=request.user)
                quizzes_created = Quiz.objects.filter(created_by=request.user)
                flashcard_sets_created = FlashcardSet.objects.filter(created_by=request.user)
                lecture_notes_created = LectureNote.objects.filter(created_by=request.user).order_by('-created_at')
                context = {
                    'teacher_classes': teacher_classes,
                    'quizzes_created': quizzes_created,
                    'flashcard_sets_created': flashcard_sets_created,
                    'lecture_notes_created': lecture_notes_created,
                }
            elif request.user.profile.user_type == 'student':
                # For students: Show classes they joined, assigned quizzes, flashcard sets, and lecture notes
                classes_joined = request.user.classes_joined.all()
                assigned_quizzes = Quiz.objects.filter(assigned_to_classes__students=request.user).distinct()
                flashcard_sets_available = FlashcardSet.objects.all() # Or filter by class later
                lecture_notes_available = LectureNote.objects.all().order_by('-created_at')
                context = {
                    'classes_joined': classes_joined,
                    'assigned_quizzes': assigned_quizzes,
                    'flashcard_sets_available': flashcard_sets_available,
                    'lecture_notes_available': lecture_notes_available,
                }
        else:
            # Fallback if profile somehow still doesn't exist after the attempt to create it
            print("DEBUG: User is authenticated but profile is still missing after creation attempt.")
            messages.warning(request, "Your profile is still missing. Functionality may be limited. Please contact support.")
            # Ensure context remains empty or minimal if profile is truly missing
            context = {}

    else: # This block is for unauthenticated users (the welcome screen)
        context = {} # Keep context empty for unauthenticated users, as no user-specific data is needed
    return render(request, 'home.html', context)

def signup(request):
    """
    Handles user registration.
    Uses the custom SignUpForm to create a User and UserProfile.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save() # Saves User and UserProfile
            login(request, user) # Log the user in immediately after signup
            messages.success(request, "Registration successful!")
            return redirect('home') # Redirect to homepage
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def create_class(request):
    """
    Allows a teacher to create a new class.
    """
    if request.method == 'POST':
        form = ClassCreationForm(request.POST)
        if form.is_valid():
            new_class = form.save(commit=False) # Don't save immediately, need to set teacher
            new_class.teacher = request.user # Set the current logged-in user as the teacher
            new_class.save() # Save the class, triggering join_code generation
            messages.success(request, f"Class '{new_class.name}' created successfully with join code: {new_class.join_code}")
            return redirect('home') # Redirect back to the homepage/teacher dashboard
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = ClassCreationForm()
    return render(request, 'classes/create_class.html', {'form': form})


@login_required
@user_passes_test(is_student)
def join_class(request):
    """
    Allows a student to join an existing class using a join code.
    """
    if request.method == 'POST':
        form = ClassJoinForm(request.POST)
        if form.is_valid():
            join_code = form.cleaned_data['join_code'].upper() # Convert to uppercase for matching
            try:
                # Find the class with the given join code
                target_class = Class.objects.get(join_code=join_code)

                # Check if the student is already in this class
                if request.user in target_class.students.all():
                    messages.info(request, f"You are already a member of '{target_class.name}'.")
                else:
                    # Add the student to the class
                    target_class.students.add(request.user)
                    messages.success(request, f"Successfully joined class '{target_class.name}'!")
                return redirect('home')
            except Class.DoesNotExist:
                messages.error(request, "Invalid join code. Please check and try again.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = ClassJoinForm()
    return render(request, 'classes/join_class.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def create_quiz(request, quiz_id=None):
    """
    Allows a teacher to create a new quiz or edit an existing one.
    Handles nested forms for questions and answers using formsets.
    """
    quiz_instance = None
    if quiz_id:
        quiz_instance = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)

    # Initialize AnswerFormSetForQuestion outside the conditional to ensure it's always defined
    AnswerFormSetForQuestion = inlineformset_factory(Question, Answer, form=AnswerForm, extra=4, can_delete=True, min_num=1, validate_min=True)

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz_instance, teacher=request.user)
        question_formset = QuestionFormSet(request.POST, instance=quiz_instance, prefix='questions')

        # Flag to track overall form validity
        all_forms_valid = True

        # Process each question form to validate its answers and collect errors
        for i, q_form in enumerate(question_formset):
            # Regardless of question form validity or deletion status, bind its answers formset
            # This ensures that validation errors are always collected and available for re-rendering
            answer_formset_prefix = f'questions-{i}-answers'
            answer_fs = AnswerFormSetForQuestion(request.POST, instance=q_form.instance if q_form.instance.pk else None, prefix=answer_formset_prefix)
            q_form.answer_formset = answer_fs # Attach to the question form for template rendering

            # Only validate if the question itself is valid and not marked for deletion
            # This prevents cascading errors from invalid/deleted questions to their answers
            if q_form.is_valid() and not q_form.cleaned_data.get('DELETE'):
                if not answer_fs.is_valid():
                    all_forms_valid = False
                    for ans_form in answer_fs.forms:
                        for field, errors in ans_form.errors.items():
                            for error in errors:
                                messages.error(request, f"Answer Error in question '{q_form.cleaned_data.get('text', '')[:50]}...': {field.capitalize()}: {error}")
                        for error in ans_form.non_field_errors():
                            messages.error(request, f"Answer Error in question '{q_form.cleaned_data.get('text', '')[:50]}...': {error}")
                    for error in answer_fs.non_form_errors():
                        messages.error(request, f"Answer Formset Error in question '{q_form.cleaned_data.get('text', '')[:50]}...': {error}")
                else: # Answer formset is valid, now check correct answer count
                    correct_answers_count = sum(1 for ans_form_obj in answer_fs.forms if ans_form_obj.cleaned_data.get('is_correct') and not ans_form_obj.cleaned_data.get('DELETE'))
                    if correct_answers_count != 1:
                        all_forms_valid = False
                        messages.error(request, f"Question '{q_form.cleaned_data.get('text', '')[:50]}...' must have exactly one correct answer.")
                        q_form.add_error(None, "Each question must have exactly one correct answer.") # Add error to specific question form


        # Check overall form validity, including the dynamically bound answer formsets
        if form.is_valid() and question_formset.is_valid() and all_forms_valid:
            with transaction.atomic():
                quiz = form.save(commit=False)
                quiz.created_by = request.user
                quiz.save()
                form.save_m2m() # Saves the assigned_to_classes relationship

                # Process questions and their answers for saving
                for i, q_form in enumerate(question_formset):
                    # Check if the question form is valid
                    if q_form.is_valid():
                        if q_form.cleaned_data.get('DELETE'): # If marked for deletion
                            if q_form.instance.pk: # Only delete if it's an existing instance
                                q_form.instance.delete()
                        else: # Not deleted, so save it
                            question = q_form.save(commit=False)
                            question.quiz = quiz
                            question.save()

                            answer_formset = q_form.answer_formset # Get the already bound/validated answer formset

                            answers_to_save = answer_formset.save(commit=False)
                            for answer_obj in answers_to_save:
                                answer_obj.question = question
                                answer_obj.save()
                            
                            # Handle deleted answers
                            for obj in answer_formset.deleted_objects:
                                obj.delete()
            messages.success(request, "Quiz saved successfully!")
            return redirect('home')
        else:
            pass
        
    else: # This block is for initial GET request
        form = QuizForm(instance=quiz_instance, teacher=request.user)
        question_formset = QuestionFormSet(instance=quiz_instance, prefix='questions')
        
    for i, question_form in enumerate(question_formset):
        question_form.answer_formset = AnswerFormSetForQuestion(
            instance=question_form.instance if question_form.instance.pk else None,
            prefix=f'questions-{i}-answers',
            data=request.POST if request.method == 'POST' else None
        )

    context = {
        'form': form,
        'question_formset': question_formset,
        'quiz_id': quiz_id, # Pass quiz_id for edit mode
    }
    return render(request, 'quizzes/create_quiz.html', context)


@login_required
@user_passes_test(is_student)
def quiz_list(request):
    """
    Displays a list of quizzes available to the logged-in student.
    These are quizzes assigned to classes the student has joined.
    """
    student_classes = request.user.classes_joined.all()
    # Get quizzes assigned to any of the student's classes
    available_quizzes = Quiz.objects.filter(assigned_to_classes__in=student_classes).distinct()

    context = {
        'available_quizzes': available_quizzes,
    }
    return render(request, 'quizzes/quiz_list.html', context)


@login_required
@user_passes_test(is_student)
def take_quiz(request, quiz_id):
    """
    Allows a student to take a specific quiz.
    Displays questions and processes answers.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().order_by('id')

    if request.method == 'POST':
        user_answers = {}
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                user_answers[question.id] = int(selected_answer_id)
            else:
                messages.warning(request, f"Please answer all questions. Question '{question.text[:50]}...' was skipped.")

        score = 0
        total_possible_points = 0
        answer_choices_to_create = []

        with transaction.atomic():
            for question in questions:
                total_possible_points += question.points
                selected_answer_id = user_answers.get(question.id)

                if selected_answer_id:
                    try:
                        chosen_answer = Answer.objects.get(id=selected_answer_id, question=question)
                        is_correct = chosen_answer.is_correct
                        if is_correct:
                            score += question.points
                        
                        answer_choices_to_create.append(
                            AnswerChoice(
                                attempt=None,
                                question=question,
                                chosen_answer=chosen_answer,
                                is_correct=is_correct
                            )
                        )
                    except Answer.DoesNotExist:
                        messages.error(request, f"Invalid answer submitted for question '{question.text[:50]}...'.")
                        raise ValueError("Invalid answer ID received.")

            quiz_attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                score=score,
                total_possible_points=total_possible_points,
            )

            for answer_choice in answer_choices_to_create:
                answer_choice.attempt = quiz_attempt
                answer_choice.save()
            
            request.user.profile.total_points += score
            request.user.profile.save()

        messages.success(request, f"You completed the quiz '{quiz.title}'! Your score: {score}/{total_possible_points}")
        return redirect('quiz_results', attempt_id=quiz_attempt.id)


@login_required
@user_passes_test(is_student)
def quiz_results(request, attempt_id):
    """
    Displays the results of a completed quiz attempt.
    """
    quiz_attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    answer_choices = quiz_attempt.chosen_answers.all().select_related('question', 'chosen_answer')

    results_details = []
    for ac in answer_choices:
        original_question = ac.question
        chosen_answer = ac.chosen_answer
        correct_answer_for_question = Answer.objects.get(question=original_question, is_correct=True)
        
        results_details.append({
            'question': original_question,
            'chosen_answer': chosen_answer,
            'correct_answer': correct_answer_for_question,
            'is_correct_for_attempt': ac.is_correct
        })

    context = {
        'quiz_attempt': quiz_attempt,
        'results_details': results_details,
    }
    return render(request, 'quizzes/quiz_results.html', context)

@login_required
@user_passes_test(is_teacher)
def create_flashcard_set(request, flashcard_set_id=None):
    """
    Allows a teacher to create a new flashcard set or edit an existing one.
    Handles nested forms for individual flashcards using formsets.
    """
    flashcard_set_instance = None
    if flashcard_set_id:
        flashcard_set_instance = get_object_or_404(FlashcardSet, id=flashcard_set_id, created_by=request.user)

    if request.method == 'POST':
        form = FlashcardSetForm(request.POST, instance=flashcard_set_instance)
        flashcard_formset = FlashcardFormSet(request.POST, instance=flashcard_set_instance, prefix='flashcards')

        if form.is_valid() and flashcard_formset.is_valid():
            with transaction.atomic():
                flashcard_set = form.save(commit=False)
                flashcard_set.created_by = request.user
                flashcard_set.save()

                flashcards_to_save = flashcard_formset.save(commit=False)
                for flashcard in flashcards_to_save:
                    flashcard.flashcard_set = flashcard_set
                    flashcard.save()
                
                for obj in flashcard_formset.deleted_objects:
                    obj.delete()

            messages.success(request, f"Flashcard Set '{flashcard_set.title}' saved successfully!")
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Flashcard Set Error: {field.capitalize()}: {error}")
            
            for error in flashcard_formset.non_form_errors():
                messages.error(request, f"Flashcard Formset Error: {error}")
            
            for f_form in flashcard_formset:
                for field, errors in f_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Flashcard Error '{f_form.instance.question[:50] if f_form.instance.pk else 'new'}': {field.capitalize()}: {error}")
    else:
        form = FlashcardSetForm(instance=flashcard_set_instance)
        flashcard_formset = FlashcardFormSet(instance=flashcard_set_instance, prefix='flashcards')

    context = {
        'form': form,
        'flashcard_formset': flashcard_formset,
        'flashcard_set_id': flashcard_set_id,
    }
    return render(request, 'flashcards/create_flashcard_set.html', context)


@login_required
@user_passes_test(is_student)
def flashcard_set_list(request):
    """
    Displays a list of all available flashcard sets for students to browse.
    This will eventually include search/filter functionality.
    """
    query = request.GET.get('q') # Get the search query from the URL parameter 'q'
    available_flashcard_sets = FlashcardSet.objects.all()

    if query:
        # Use Q objects for OR conditions across multiple fields
        available_flashcard_sets = available_flashcard_sets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(subject__icontains=query) |
            Q(topic__icontains=query) |
            Q(year_group__icontains=query) |
            Q(created_by__username__icontains=query) # Search by creator's username
        ).distinct() # Use distinct to avoid duplicates if a set matches multiple criteria

    available_flashcard_sets = available_flashcard_sets.order_by('title')

    context = {
        'available_flashcard_sets': available_flashcard_sets,
        'query': query # Pass the query back to the template to pre-fill the search box
    }
    return render(request, 'flashcards/flashcard_set_list.html', context)


@login_required
@user_passes_test(is_student)
def study_flashcard_set(request, flashcard_set_id):
    """
    Allows a student to study a specific flashcard set.
    Presents flashcards one by one.
    """
    flashcard_set = get_object_or_404(FlashcardSet, id=flashcard_set_id)
    flashcards = list(flashcard_set.flashcards.all().order_by('id'))

    session_key = f'flashcard_session_{flashcard_set_id}'
    if session_key not in request.session:
        request.session[session_key] = {
            'current_card_index': 0,
            'known_cards': [],
            'unknown_cards': [],
            'total_cards': len(flashcards),
            'started_at': None
        }
        request.session[session_key]['unknown_cards'] = [fc.id for fc in flashcards]

    if request.method == 'POST':
        session_data = request.session[session_key]
        action = request.POST.get('action')
        card_id = int(request.POST.get('card_id')) if request.POST.get('card_id') else None

        if action == 'mark_known' and card_id is not None:
            if card_id in session_data['unknown_cards']:
                session_data['unknown_cards'].remove(card_id)
                session_data['known_cards'].append(card_id)
                messages.success(request, "Card marked as known!")
        elif action == 'mark_unknown' and card_id is not None:
            if card_id in session_data['known_cards']:
                session_data['known_cards'].remove(card_id)
                session_data['unknown_cards'].append(card_id)
                messages.info(request, "Card marked as unknown (will reappear).")
        elif action == 'next_card':
            session_data['current_card_index'] += 1
        elif action == 'previous_card':
            if session_data['current_card_index'] > 0:
                session_data['current_card_index'] -= 1
        elif action == 'restart_session':
             request.session[session_key] = {
                'current_card_index': 0,
                'known_cards': [],
                'unknown_cards': [fc.id for fc in flashcards],
                'total_cards': len(flashcards),
                'started_at': None
            }
             messages.info(request, "Flashcard session restarted!")

        request.session.modified = True
        return redirect('study_flashcard_set', flashcard_set_id=flashcard_set_id)

    session_data = request.session[session_key]
    current_card_index = session_data['current_card_index']

    current_flashcard = None
    if current_card_index < len(flashcards):
        current_flashcard = flashcards[current_card_index]

    last_card_index = len(flashcards) - 1

    context = {
        'flashcard_set': flashcard_set,
        'current_flashcard': current_flashcard,
        'current_card_index': current_card_index,
        'total_cards': len(flashcards),
        'known_count': len(session_data['known_cards']),
        'unknown_count': len(session_data['unknown_cards']),
        'is_session_complete': len(session_data['unknown_cards']) == 0 and len(flashcards) > 0,
        'last_card_index': last_card_index,
    }
    return render(request, 'flashcards/study_flashcard_set.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_quiz_dashboard(request, quiz_id):
    """
    Displays a dashboard for a specific quiz, showing analytics and student progress.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    
    # Overall Quiz Analytics
    all_attempts = QuizAttempt.objects.filter(quiz=quiz)
    
    total_attempts = all_attempts.count()
    average_score = all_attempts.aggregate(Avg('score'))['score__avg']
    
    # Student Progress Tracking for this Quiz
    student_attempts = []
    # Get distinct students who attempted this quiz
    students_who_attempted = all_attempts.values_list('student__username', flat=True).distinct()
    
    for student_username in students_who_attempted:
        student_user = get_object_or_404(request.user.__class__, username=student_username)
        # Get all attempts by this student for this quiz, ordered by date (most recent first)
        attempts_by_student = all_attempts.filter(student=student_user).order_by('-completed_at')
        
        student_attempts.append({
            'student_username': student_user.username,
            'attempts': attempts_by_student
        })

    # Per-Question Analytics
    questions = quiz.questions.all().order_by('id')
    question_analytics = []

    for question in questions:
        total_question_attempts = AnswerChoice.objects.filter(question=question, attempt__quiz=quiz).count()
        correct_choices = AnswerChoice.objects.filter(
            question=question,
            attempt__quiz=quiz,
            is_correct=True
        ).count()
        
        # Calculate percentage correct for this question
        percentage_correct = (correct_choices / total_question_attempts * 100) if total_question_attempts > 0 else 0

        # Get all possible answers for this question
        all_answers_for_question = Answer.objects.filter(question=question)
        answer_breakdown = []
        for answer in all_answers_for_question:
            times_chosen = AnswerChoice.objects.filter(
                question=question,
                chosen_answer=answer,
                attempt__quiz=quiz
            ).count()
            answer_breakdown.append({
                'answer_text': answer.text,
                'is_correct': answer.is_correct,
                'times_chosen': times_chosen,
                'percentage_chosen': (times_chosen / total_question_attempts * 100) if total_question_attempts > 0 else 0
            })
        
        question_analytics.append({
            'question': question,
            'total_question_attempts': total_question_attempts,
            'correct_choices': correct_choices,
            'percentage_correct': round(percentage_correct, 2),
            'answer_breakdown': answer_breakdown
        })

    context = {
        'quiz': quiz,
        'total_attempts': total_attempts,
        'average_score': round(average_score, 2) if average_score is not None else 'N/A',
        'student_attempts': student_attempts,
        'question_analytics': question_analytics,
    }
    return render(request, 'quizzes/teacher_quiz_dashboard.html', context)


@login_required
def leaderboard(request):
    """
    Displays a leaderboard of all users ranked by their total_points.
    """
    # Fetch all UserProfiles, order by total_points descending.
    # Select related User to get username directly.
    top_students = UserProfile.objects.select_related('user').order_by('-total_points')

    context = {
        'top_students': top_students,
    }
    return render(request, 'leaderboard.html', context)


# VIEWS FOR LECTURE NOTES
@login_required
@user_passes_test(is_teacher)
def create_lecture_note(request, note_id=None):
    """
    Allows a teacher to create a new lecture note or edit an existing one.
    """
    note_instance = None
    if note_id:
        note_instance = get_object_or_404(LectureNote, id=note_id, created_by=request.user)

    if request.method == 'POST':
        form = LectureNoteForm(request.POST, instance=note_instance)
        if form.is_valid():
            lecture_note = form.save(commit=False)
            lecture_note.created_by = request.user
            lecture_note.save()
            messages.success(request, f"Lecture Note '{lecture_note.title}' saved successfully!")
            return redirect('lecture_note_list') # Redirect to list of notes
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Note Error: {field.capitalize()}: {error}")
    else:
        form = LectureNoteForm(instance=note_instance)
    
    context = {
        'form': form,
        'note_id': note_id,
    }
    return render(request, 'notes/create_lecture_note.html', context)


@login_required
def lecture_note_list(request):
    """
    Displays a list of all available lecture notes for all authenticated users.
    Teachers can see their own, students can see all published notes.
    """
    notes = LectureNote.objects.all().order_by('-created_at') # Order by newest first
    context = {
        'notes': notes,
    }
    return render(request, 'notes/lecture_note_list.html', context)


@login_required
def view_lecture_note(request, note_id):
    """
    Displays a single lecture note, rendering its content with Markdown.
    Accessible by all authenticated users.
    """
    lecture_note = get_object_or_404(LectureNote, id=note_id)
    # Render markdown content to HTML
    # Using extensions like 'fenced_code' for code blocks, 'extra' for more markdown features
    rendered_content = markdown.markdown(lecture_note.content, extensions=['fenced_code', 'extra', 'tables'])

    context = {
        'lecture_note': lecture_note,
        'rendered_content': rendered_content,
    }
    return render(request, 'notes/view_lecture_note.html', context)
