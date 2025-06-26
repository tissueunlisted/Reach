# C:\entc\core_app\models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid # For generating unique join codes
# Removed: from django.utils import timezone # No longer needed for temporary default

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    total_points = models.IntegerField(default=0) # For gamification/leaderboards

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.user_type})"

# Signal to create or update user profile when a User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()

class Class(models.Model):
    name = models.CharField(max_length=100)
    join_code = models.CharField(max_length=8, unique=True, blank=True) # Final state: non-nullable, unique
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes_taught')
    students = models.ManyToManyField(User, related_name='classes_joined', blank=True)

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = str(uuid.uuid4())[:8].upper() # Generate a unique 8-char code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Final state: non-nullable
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    year_group = models.CharField(max_length=50) # e.g., "Year 7", "Sophomore"
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes_created') # Final state: non-nullable
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to_classes = models.ManyToManyField(Class, related_name='assigned_quizzes', blank=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.IntegerField(default=1) # Points for answering this question correctly

    def __str__(self):
        return f"Q: {self.text[:50]}..." # Show first 50 chars of question text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Ans: {self.text[:50]}... ({'Correct' if self.is_correct else 'Incorrect'})"

class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()
    total_possible_points = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_spent_seconds = models.IntegerField(null=True, blank=True) # Optional: track time spent

    @property
    def accuracy(self):
        if self.total_possible_points == 0:
            return 0
        return (self.score / self.total_possible_points) * 100

    def __str__(self):
        return f"{self.student.username}'s attempt on {self.quiz.title} ({self.score}/{self.total_possible_points})"

class AnswerChoice(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='chosen_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='chosen_by_students')
    chosen_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='chosen_in_attempts')
    is_correct = models.BooleanField() # Stores whether the chosen answer was correct for that question

    def __str__(self):
        return f"Attempt {self.attempt.id}: Q'{self.question.text[:20]}...' chose '{self.chosen_answer.text[:20]}...' ({'Correct' if self.is_correct else 'Incorrect'})"

class FlashcardSet(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Final state: non-nullable
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    year_group = models.CharField(max_length=50)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_sets_created') # Final state: non-nullable
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='flashcards')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) # Final state: auto_now_add only
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q: {self.question[:50]}... A: {self.answer[:50]}..."

class FlashcardEngagement(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_engagements')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE) # Final state: non-nullable
    status = models.CharField(max_length=20, default='new')
    last_practiced = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'flashcard') # Final state: unique_together should refer to existing fields

    def __str__(self):
        return f"{self.student.username} - {self.flashcard.id} ({self.status})"


# NEW MODEL: LectureNote
class LectureNote(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_notes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
