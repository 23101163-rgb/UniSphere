from django import forms
from .models import (
    ResearchGroup, ResearchGroupInvitation,
    SupervisorRequest, KnowledgeAssessment, AssessmentQuestion,
    ReferencePaper, ResearchPaper, PaperReview
)
from accounts.models import User


class ResearchGroupForm(forms.ModelForm):
    class Meta:
        model = ResearchGroup
        fields = ['name', 'description', 'research_area', 'group_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'


class ResearchGroupInvitationForm(forms.ModelForm):
    class Meta:
        model = ResearchGroupInvitation
        fields = ['invited_user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invited_user'].queryset = User.objects.filter(role__in=['student', 'alumni'])
        self.fields['invited_user'].label = 'Select Student / Alumni'
        self.fields['invited_user'].widget.attrs['class'] = 'form-control'


class SupervisorRequestForm(forms.Form):
    faculty = forms.ModelChoiceField(
        queryset=User.objects.filter(role='teacher'),
        label='Select Faculty Member',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Why do you want this faculty as supervisor?'
        }),
        required=False
    )


class TopicSelectionForm(forms.Form):
    research_topic = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter research topic for this group'
        })
    )


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = KnowledgeAssessment
        fields = ['title', 'passing_score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'


class AssessmentQuestionForm(forms.ModelForm):
    class Meta:
        model = AssessmentQuestion
        fields = [
            'question_text', 'option_a', 'option_b',
            'option_c', 'option_d', 'correct_option'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'
        self.fields['question_text'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 2}
        )


class ReferencePaperForm(forms.ModelForm):
    class Meta:
        model = ReferencePaper
        fields = ['title', 'url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'
        self.fields['url'].widget.attrs['placeholder'] = 'https://scholar.google.com/...'


class ResearchPaperForm(forms.ModelForm):
    class Meta:
        model = ResearchPaper
        fields = ['title', 'abstract', 'document']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'


class PaperReviewForm(forms.ModelForm):
    class Meta:
        model = PaperReview
        fields = ['feedback', 'is_approved']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['feedback'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 4}
        )
        self.fields['is_approved'].widget.attrs['class'] = 'form-check-input'