from django import forms
from .models import Event


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
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name not in ('date', 'time'):
                field.widget.attrs['class'] = 'form-control'

        self.fields['club_name'].required = False
        self.fields['registration_link'].required = False