from django import forms
from .models import ThesisResource, MentorshipRequest, ResearchGroup

class ThesisResourceForm(forms.ModelForm):
    class Meta:
        model = ThesisResource
        fields = ['title', 'abstract', 'authors', 'year', 'research_area', 'document']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs['class'] = 'form-control'

class MentorshipRequestForm(forms.ModelForm):
    class Meta:
        model = MentorshipRequest
        fields = ['topic', 'message']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs['class'] = 'form-control'

class ResearchGroupForm(forms.ModelForm):
    class Meta:
        model = ResearchGroup
        fields = ['name', 'description', 'research_area']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs['class'] = 'form-control'
