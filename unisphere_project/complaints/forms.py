from django import forms
from .models import Complaint
from accounts.models import User

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['target_type', 'target_teacher', 'subject', 'description', 'category', 'is_anonymous']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if name == 'is_anonymous':
                f.widget.attrs['class'] = 'form-check-input'
            else:
                f.widget.attrs['class'] = 'form-control'

        # Teacher dropdown - only show teachers
        self.fields['target_teacher'].queryset = User.objects.filter(role='teacher')
        self.fields['target_teacher'].required = False
        self.fields['target_teacher'].empty_label = '-- Select Teacher --'

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get('target_type')
        target_teacher = cleaned_data.get('target_teacher')
        if target_type == 'teacher' and not target_teacher:
            self.add_error('target_teacher', 'Please select a teacher.')
        return cleaned_data

class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'admin_response']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs['class'] = 'form-control'