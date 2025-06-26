# C:\entc\core_app\forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms import inlineformset_factory
from .models import (
    User,
    UserProfile, # Ensure UserProfile is imported
    Class,
    Quiz,
    Question,
    Answer,
    FlashcardSet,
    Flashcard,
    LectureNote
)

class SignUpForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True) # Make email required

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.save() # User is saved here, triggering the post_save signal immediately

        # The post_save signal should have already created the UserProfile.
        # Now, we just update its user_type.
        user_profile = user.profile # Access the profile created by the signal
        user_profile.user_type = self.cleaned_data['user_type']
        user_profile.save() # Save the updated user_type to the profile

        return user

class ClassCreationForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter class name'}),
        }

class ClassJoinForm(forms.Form):
    join_code = forms.CharField(max_length=8, help_text="Enter the 8-character join code provided by your teacher.",
                                widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., ABC123DE'}))

class QuizForm(forms.ModelForm):
    assigned_to_classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Assign to Classes"
    )

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'subject', 'topic', 'year_group', 'assigned_to_classes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Algebra Basics Quiz'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Briefly describe the quiz content...', 'rows': 3}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Mathematics'}),
            'topic': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Equations'}),
            'year_group': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Year 9'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['assigned_to_classes'].queryset = Class.objects.filter(teacher=teacher)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Enter question text', 'rows': 2}),
            'points': forms.NumberInput(attrs={'class': 'form-input'}),
        }

QuestionFormSet = inlineformset_factory(Quiz, Question, form=QuestionForm, extra=1, can_delete=True)

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter answer option'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class FlashcardSetForm(forms.ModelForm):
    class Meta:
        model = FlashcardSet
        fields = ['title', 'description', 'subject', 'topic', 'year_group']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., French Vocabulary'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Briefly describe this flashcard set...', 'rows': 3}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Languages'}),
            'topic': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Food & Drink'}),
            'year_group': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Year 8'}),
        }

class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ['question', 'answer']
        widgets = {
            'question': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Front of card (Question)', 'rows': 2}),
            'answer': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Back of card (Answer)', 'rows': 2}),
        }

FlashcardFormSet = inlineformset_factory(FlashcardSet, Flashcard, form=FlashcardForm, extra=1, can_delete=True)


class LectureNoteForm(forms.ModelForm):
    class Meta:
        model = LectureNote
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Introduction to Photosynthesis'}),
            'content': forms.Textarea(attrs={'class': 'form-textarea min-h-[300px]', 'placeholder': 'Write your lecture notes here... Supports basic Markdown (e.g., **bold**, *italics*, # Heading)', 'rows': 15}),
        }
