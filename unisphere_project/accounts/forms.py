from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='University Email'
    )
    role = forms.ChoiceField(
        choices=[
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('alumni', 'Alumni'),
        ]
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'university_id',
            'first_name',
            'last_name',
            'role',
            'profile_picture',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your UAP email'
        self.fields['university_id'].widget.attrs['placeholder'] = 'Enter university ID'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

        self.fields['profile_picture'].label = 'Profile Picture (Optional)'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise forms.ValidationError('Email is required.')

        if not email.endswith('@uap-bd.edu'):
            raise forms.ValidationError('Please use your university email (@uap-bd.edu).')

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')

        return email

    def clean_university_id(self):
        university_id = self.cleaned_data.get('university_id', '').strip()

        if not university_id:
            raise forms.ValidationError('University ID is required.')

        if User.objects.filter(university_id=university_id).exists():
            raise forms.ValidationError('This university ID is already registered.')

        return university_id

    def clean_role(self):
        role = self.cleaned_data.get('role')
        valid_roles = ['student', 'teacher', 'alumni']

        if role not in valid_roles:
            raise forms.ValidationError('Please select a valid role.')

        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '').strip().lower()
        user.university_id = self.cleaned_data.get('university_id', '').strip()
        user.first_name = self.cleaned_data.get('first_name', '').strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.role = self.cleaned_data.get('role')

        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            user.profile_picture = profile_picture

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'bio',
            'profile_picture',
            'semester',
            'research_interests',
            'expertise',
            'graduation_year',
            'company',
            'designation',
            'is_mentor_available'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        self.fields['is_mentor_available'].widget.attrs['class'] = 'form-check-input'
        self.fields['profile_picture'].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise forms.ValidationError('Email is required.')

        existing_user = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).first()
        if existing_user:
            raise forms.ValidationError('This email is already in use by another account.')

        return email