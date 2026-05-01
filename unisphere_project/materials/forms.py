from django import forms
from .models import StudyMaterial, MaterialRating


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = [
            'title',
            'description',
            'course_name',
            'semester',
            'topic',
            'tags',
            'file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter material title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a short description'
            }),
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course name, e.g. CSE101'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-select'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter topic name'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. oop, python, final, notes'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'tags': 'Use comma-separated tags for easier search.'
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Title is required.')
        return title

    def clean_course_name(self):
        course_name = self.cleaned_data.get('course_name', '').strip()
        if not course_name:
            raise forms.ValidationError('Course name is required.')
        return course_name.upper()

    def clean_topic(self):
        topic = self.cleaned_data.get('topic', '').strip()
        if not topic:
            raise forms.ValidationError('Topic is required.')
        return topic

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '').strip()
        return tags

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('Please upload a file.')

        max_size = 10 * 1024 * 1024  # 10 MB
        if file.size > max_size:
            raise forms.ValidationError('File size must be under 10 MB.')

        return file


class MaterialRatingForm(forms.ModelForm):
    class Meta:
        model = MaterialRating
        fields = ['score', 'review']
        widgets = {
            'score': forms.Select(attrs={
                'class': 'form-select'
            }),
            'review': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your feedback (optional)'
            }),
        }

    def clean_review(self):
        review = self.cleaned_data.get('review', '').strip()
        return review