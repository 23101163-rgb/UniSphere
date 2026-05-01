from django import forms
from django.utils import timezone

from .models import Event, EventRegistration


class EventForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'organizer_category',
            'club_name',
            'event_type',
            'date',
            'time',
            'venue',
            'registration_link'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name not in ('date', 'time'):
                field.widget.attrs['class'] = 'form-control'

        self.fields['club_name'].required = False
        self.fields['registration_link'].required = False

        if self.user and not (self.user.is_admin_user() or self.user.is_teacher()):
            authorized_clubs = self.user.get_authorized_club_names()
            self.fields['club_name'].choices = [
                choice for choice in self.fields['club_name'].choices
                if choice[0] in authorized_clubs
            ]

    def clean_date(self):
        event_date = self.cleaned_data.get('date')

        if event_date and event_date < timezone.localdate():
            raise forms.ValidationError('The date has passed')

        return event_date

    def clean(self):
        cleaned_data = super().clean()

        organizer_category = cleaned_data.get('organizer_category')
        club_name = cleaned_data.get('club_name')

        if organizer_category == 'club':
            if not club_name:
                self.add_error('club_name', 'Please select a club.')
            elif self.user and not self.user.can_post_for_club(club_name):
                self.add_error(
                    'club_name',
                    'You can upload events only for your authorized club.'
                )
        else:
            cleaned_data['club_name'] = ''

        return cleaned_data


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = [
            'full_name',
            'email',
            'phone',
            'department',
            'university_id',
            'note'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['phone'].widget.attrs.update({
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': 'Example: 01712345678'
        })

        self.fields['university_id'].widget.attrs.update({
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': 'Example: 23101163'
        })

        self.fields['note'].widget = forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional note'
            }
        )

        if user:
            self.fields['full_name'].initial = user.get_full_name()
            self.fields['email'].initial = user.email
            self.fields['department'].initial = user.department
            self.fields['university_id'].initial = user.university_id

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()

        if phone and not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only numbers.')

        return phone

    def clean_university_id(self):
        university_id = (self.cleaned_data.get('university_id') or '').strip()

        if university_id and not university_id.isdigit():
            raise forms.ValidationError('University ID must contain only numbers.')

        return university_id