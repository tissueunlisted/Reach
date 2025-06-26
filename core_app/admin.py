# C:\entc\core_app\admin.py

from django.contrib import admin
from .models import (
    UserProfile, Class, Quiz, Question, Answer, QuizAttempt, AnswerChoice,
    FlashcardSet, Flashcard, FlashcardEngagement, LectureNote # Ensure LectureNote is imported
)

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Removed 'profile_color_hex' as it does not exist in the model
    list_display = ('user', 'user_type', 'total_points') 
    list_filter = ('user_type',)
    search_fields = ('user__username', 'user__email')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'join_code')
    list_filter = ('teacher',)
    search_fields = ('name', 'join_code', 'teacher__username')
    readonly_fields = ('join_code',) # join_code is auto-generated

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'topic', 'created_by', 'created_at')
    list_filter = ('subject', 'topic', 'year_group', 'created_by')
    search_fields = ('title', 'description', 'subject', 'topic')
    filter_horizontal = ('assigned_to_classes',) # Allows multi-select for classes in admin

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'points')
    list_filter = ('quiz',)
    search_fields = ('text',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    list_filter = ('question__quiz', 'is_correct') # Filter by quiz of the question
    search_fields = ('text',)

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total_possible_points', 'completed_at', 'accuracy')
    list_filter = ('quiz', 'student')
    search_fields = ('student__username', 'quiz__title')
    # All fields are read-only as attempts are records of past actions
    readonly_fields = ('student', 'quiz', 'score', 'total_possible_points', 'completed_at', 'time_spent_seconds')

@admin.register(AnswerChoice)
class AnswerChoiceAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'chosen_answer', 'is_correct')
    list_filter = ('attempt__quiz', 'question', 'is_correct') # Filter by quiz of the attempt's question
    readonly_fields = ('attempt', 'question', 'chosen_answer', 'is_correct') # All fields are read-only

@admin.register(FlashcardSet)
class FlashcardSetAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'topic', 'created_by', 'created_at')
    list_filter = ('subject', 'topic', 'year_group', 'created_by')
    search_fields = ('title', 'description', 'subject', 'topic')

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('flashcard_set', 'question', 'answer', 'created_at')
    list_filter = ('flashcard_set',)
    search_fields = ('question', 'answer')

@admin.register(FlashcardEngagement)
class FlashcardEngagementAdmin(admin.ModelAdmin):
    # Corrected list_display:
    # 'flashcard_set' replaced by custom method 'get_flashcard_set_title'
    # 'last_reviewed' replaced by 'last_practiced' (actual field name)
    # 'review_count' removed as it's not a field/method on the model
    list_display = ('student', 'get_flashcard_set_title', 'status', 'last_practiced')
    
    # Corrected list_filter: filters by the title of the flashcard set linked via 'flashcard'
    list_filter = ('status', 'flashcard__flashcard_set__title') 
    
    search_fields = ('student__username', 'flashcard__question', 'flashcard__flashcard_set__title')
    
    # Corrected readonly_fields: 'last_reviewed' replaced by 'last_practiced', 'review_count' removed
    readonly_fields = ('student', 'flashcard', 'status', 'last_practiced')

    # Custom method to display the FlashcardSet title for FlashcardEngagement
    # This is necessary because FlashcardEngagement has a FK to Flashcard, not directly to FlashcardSet
    def get_flashcard_set_title(self, obj):
        if obj.flashcard and obj.flashcard.flashcard_set:
            return obj.flashcard.flashcard_set.title
        return "N/A"
    get_flashcard_set_title.short_description = 'Flashcard Set' # Sets the column header in admin list view


# NEW ADMIN REGISTRATION FOR LectureNote
@admin.register(LectureNote)
class LectureNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_by',)
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at') # These fields are typically auto-set
