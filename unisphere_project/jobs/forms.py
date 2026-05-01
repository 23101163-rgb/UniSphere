from django import forms
from django.utils import timezone

from .models import JobListing, JobApplication


class JobListingForm(forms.ModelForm):
    application_deadline = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    class Meta:
        model = JobListing
        fields = [
            'title',
            'company_name',
            'job_type',
            'description',
            'required_skills',
            'eligibility',
            'salary_range',
            'application_deadline',
            'application_link'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name != 'application_deadline':
                field.widget.attrs['class'] = 'form-control'

        self.fields['salary_range'].widget.attrs.update({
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': 'Example: 25000'
        })

    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')

        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError('The date has passed')

        return deadline

    def clean_salary_range(self):
        salary = (self.cleaned_data.get('salary_range') or '').strip()

        if salary and not salary.isdigit():
            raise forms.ValidationError('Salary must contain only numbers.')

        return salary


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'full_name',
            'email',
            'phone',
            'cover_letter',
            'cv_link'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['phone'].widget.attrs.update({
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': 'Example: 01712345678'
        })

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()

        if phone and not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only numbers.')

        return phone