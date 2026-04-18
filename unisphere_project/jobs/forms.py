from django import forms
from .models import JobListing,JobApplication

class JobListingForm(forms.ModelForm):
    application_deadline = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class Meta:
        model = JobListing
        fields = ['title', 'company_name', 'job_type', 'description', 'required_skills', 'eligibility', 'salary_range', 'application_deadline', 'application_link']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if name != 'application_deadline':
                f.widget.attrs['class'] = 'form-control'
class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['full_name', 'email', 'phone', 'cover_letter', 'cv_link']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'