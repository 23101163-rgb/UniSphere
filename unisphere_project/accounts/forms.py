from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.text import slugify

from .models import User, ClubMembership, TeacherCourseAssignment


TEACHER_COURSE_HELP_TEXT = (
    'Add one course per line using this format: Semester - Course Code. '
    'Example: 1.1 - CSE101'
)

CLUB_POSITION_FIELD_PREFIX = 'club_position_for_'


def parse_teacher_course_lines(value):
    """Parse multi-line teacher courses into [(semester, course_name), ...]."""
    assignments = []
    value = value or ''

    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue

        if '-' in line:
            semester, course_name = line.split('-', 1)
        elif ',' in line:
            semester, course_name = line.split(',', 1)
        else:
            raise forms.ValidationError(
                'Each teacher course must be like: 1.1 - CSE101'
            )

        semester = semester.strip()
        course_name = course_name.strip().upper()

        valid_semesters = [choice[0] for choice in User.SEMESTER_CHOICES]
        if semester not in valid_semesters:
            raise forms.ValidationError(
                f'Invalid semester "{semester}". Use values like 1.1, 1.2, 2.1.'
            )

        if not course_name:
            raise forms.ValidationError('Course name cannot be empty.')

        assignments.append((semester, course_name))

    seen = set()
    unique_assignments = []

    for assignment in assignments:
        if assignment not in seen:
            seen.add(assignment)
            unique_assignments.append(assignment)

    return unique_assignments


def format_teacher_course_lines(assignments):
    return '\n'.join(f'{semester} - {course}' for semester, course in assignments)


def club_position_field_name(club_name):
    """
    Create a safe dynamic form field name for each club.
    Example: UAP Programming Contest Club -> club_position_for_uap_programming_contest_club
    """
    return f'{CLUB_POSITION_FIELD_PREFIX}{slugify(club_name).replace("-", "_")}'


def get_club_position_choices():
    choices = list(User.CLUB_POSITION_CHOICES)

    if choices and choices[0][0] == '':
        return choices

    return [('', 'Select Position')] + choices


def get_club_choices_without_blank():
    return [choice for choice in User.CLUB_CHOICES if choice[0]]


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

    teacher_course_name = forms.CharField(
        required=False,
        label='Teacher Courses',
        help_text=TEACHER_COURSE_HELP_TEXT,
        widget=forms.Textarea(attrs={'rows': 3})
    )

    is_club_member = forms.BooleanField(
        required=False,
        label='Are you a club member?'
    )

    club_names = forms.MultipleChoiceField(
        required=False,
        label='Select Club(s)',
        choices=get_club_choices_without_blank(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'university_id',
            'first_name',
            'last_name',
            'role',
            'teacher_course_name',
            'profile_picture',
            'is_club_member',
            'club_names',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.club_position_field_map = {}

        for club_value, club_label in get_club_choices_without_blank():
            position_field_name = club_position_field_name(club_value)
            self.club_position_field_map[club_value] = position_field_name

            self.fields[position_field_name] = forms.ChoiceField(
                required=False,
                label=f'{club_label} Position',
                choices=get_club_position_choices()
            )

            self.fields[position_field_name].widget.attrs.update({
                'class': 'form-control club-position-select',
                'data-club-position-for': club_value
            })

        for name, field in self.fields.items():
            if name == 'club_names':
                field.widget.attrs['class'] = 'club-checkbox-input'
            elif name.startswith(CLUB_POSITION_FIELD_PREFIX):
                field.widget.attrs.update({
                    'class': 'form-control club-position-select',
                    'data-club-position-for': self._get_club_value_from_position_field(name)
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your UAP email'
        self.fields['university_id'].widget.attrs['placeholder'] = 'Enter university ID'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter password'

        self.fields['teacher_course_name'].widget.attrs['placeholder'] = (
            'Example:\n'
            '1.1 - CSE101\n'
            '1.2 - CSE102\n'
            '2.1 - CSE201'
        )

        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

        self.fields['profile_picture'].label = 'Profile Picture (Optional)'
        self.fields['username'].validators = []

        dynamic_position_fields = list(self.club_position_field_map.values())

        self.order_fields([
            'username',
            'email',
            'university_id',
            'first_name',
            'last_name',
            'role',
            'teacher_course_name',
            'profile_picture',
            'is_club_member',
            'club_names',
            *dynamic_position_fields,
            'password1',
            'password2',
        ])

    def _get_club_value_from_position_field(self, field_name):
        for club_value, position_field_name in getattr(self, 'club_position_field_map', {}).items():
            if position_field_name == field_name:
                return club_value
        return ''

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

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get('role')
        teacher_course_name = cleaned_data.get('teacher_course_name', '').strip()

        is_club_member = cleaned_data.get('is_club_member')
        club_names = cleaned_data.get('club_names') or []

        if role == 'teacher':
            if not teacher_course_name:
                self.add_error(
                    'teacher_course_name',
                    'At least one course is required for teachers.'
                )
            else:
                try:
                    assignments = parse_teacher_course_lines(teacher_course_name)

                    if not assignments:
                        self.add_error(
                            'teacher_course_name',
                            'At least one course is required for teachers.'
                        )
                    else:
                        cleaned_data['teacher_course_assignments'] = assignments
                        cleaned_data['teacher_course_name'] = format_teacher_course_lines(assignments)

                except forms.ValidationError as exc:
                    self.add_error('teacher_course_name', exc)
        else:
            cleaned_data['teacher_course_name'] = ''
            cleaned_data['teacher_course_assignments'] = []

        club_positions = {}

        if is_club_member:
            if not club_names:
                self.add_error('club_names', 'Please select at least one club.')

            for club_name in club_names:
                position_field_name = club_position_field_name(club_name)
                position = cleaned_data.get(position_field_name)

                if not position:
                    club_label = dict(User.CLUB_CHOICES).get(club_name, club_name)
                    self.add_error(
                        position_field_name,
                        f'Please select your position for {club_label}.'
                    )
                else:
                    club_positions[club_name] = position
        else:
            cleaned_data['club_names'] = []

        cleaned_data['club_positions'] = club_positions

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data.get('email', '').strip().lower()
        user.university_id = self.cleaned_data.get('university_id', '').strip()
        user.first_name = self.cleaned_data.get('first_name', '').strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.role = self.cleaned_data.get('role')

        teacher_assignments = self.cleaned_data.get('teacher_course_assignments', [])
        user.teacher_course_name = teacher_assignments[0][1] if teacher_assignments else ''

        user.is_club_member = self.cleaned_data.get('is_club_member', False)

        club_names = self.cleaned_data.get('club_names', [])
        club_positions = self.cleaned_data.get('club_positions', {})

        user.club_name = club_names[0] if club_names else ''
        user.club_position = club_positions.get(user.club_name, '') if user.club_name else ''

        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            user.profile_picture = profile_picture

        if commit:
            user.save()

            if user.is_teacher():
                TeacherCourseAssignment.objects.filter(teacher=user).delete()

                for semester, course_name in teacher_assignments:
                    TeacherCourseAssignment.objects.create(
                        teacher=user,
                        semester=semester,
                        course_name=course_name
                    )

            if user.is_club_member:
                ClubMembership.objects.filter(user=user).delete()

                for club_name in club_names:
                    ClubMembership.objects.create(
                        user=user,
                        club_name=club_name,
                        club_position=club_positions.get(club_name, ''),
                        is_verified=False,
                        authorized_to_post=True
                    )
            else:
                ClubMembership.objects.filter(user=user).delete()

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
    club_names = forms.MultipleChoiceField(
        required=False,
        label='Select Club(s)',
        choices=get_club_choices_without_blank(),
        widget=forms.CheckboxSelectMultiple
    )

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
            'teacher_course_name',
            'research_interests',
            'expertise',
            'graduation_year',
            'company',
            'designation',
            'is_mentor_available',
            'is_club_member',
            'club_names',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.club_position_field_map = {}

        existing_memberships = {}
        existing_clubs = []

        if self.instance and self.instance.pk:
            if self.instance.role == 'teacher':
                assignments = self.instance.get_teacher_course_assignments()

                semester_assignments = [
                    (sem, course) for sem, course in assignments if sem
                ]

                self.fields['teacher_course_name'].initial = format_teacher_course_lines(
                    semester_assignments
                )

            existing_clubs = self.instance.get_club_names_for_profile()
            self.fields['club_names'].initial = existing_clubs

            existing_memberships = {
                membership.club_name: membership.club_position
                for membership in ClubMembership.objects.filter(user=self.instance)
            }

        for club_value, club_label in get_club_choices_without_blank():
            position_field_name = club_position_field_name(club_value)
            self.club_position_field_map[club_value] = position_field_name

            initial_position = existing_memberships.get(club_value, '')

            if not initial_position and self.instance and self.instance.club_name == club_value:
                initial_position = self.instance.club_position

            self.fields[position_field_name] = forms.ChoiceField(
                required=False,
                label=f'{club_label} Position',
                choices=get_club_position_choices(),
                initial=initial_position
            )

            self.fields[position_field_name].widget.attrs.update({
                'class': 'form-control club-position-select',
                'data-club-position-for': club_value
            })

        for name, field in self.fields.items():
            if name == 'club_names':
                field.widget.attrs['class'] = 'club-checkbox-input'
            elif name.startswith(CLUB_POSITION_FIELD_PREFIX):
                field.widget.attrs.update({
                    'class': 'form-control club-position-select',
                    'data-club-position-for': self._get_club_value_from_position_field(name)
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        self.fields['profile_picture'].widget.attrs['class'] = 'form-control'

        self.fields['teacher_course_name'].required = False
        self.fields['teacher_course_name'].label = 'Teacher Courses'
        self.fields['teacher_course_name'].help_text = TEACHER_COURSE_HELP_TEXT

        self.fields['teacher_course_name'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': (
                'Example:\n'
                '1.1 - CSE101\n'
                '1.2 - CSE102\n'
                '2.1 - CSE201'
            )
        })

        dynamic_position_fields = list(self.club_position_field_map.values())

        self.order_fields([
            'first_name',
            'last_name',
            'email',
            'phone',
            'bio',
            'profile_picture',
            'semester',
            'teacher_course_name',
            'research_interests',
            'expertise',
            'graduation_year',
            'company',
            'designation',
            'is_mentor_available',
            'is_club_member',
            'club_names',
            *dynamic_position_fields,
        ])

    def _get_club_value_from_position_field(self, field_name):
        for club_value, position_field_name in getattr(self, 'club_position_field_map', {}).items():
            if position_field_name == field_name:
                return club_value
        return ''

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise forms.ValidationError('Email is required.')

        existing_user = User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk).first()

        if existing_user:
            raise forms.ValidationError('This email is already in use by another account.')

        return email

    def clean(self):
        cleaned_data = super().clean()

        teacher_course_name = cleaned_data.get('teacher_course_name', '').strip()

        is_club_member = cleaned_data.get('is_club_member')
        club_names = cleaned_data.get('club_names') or []

        if self.instance and self.instance.role == 'teacher':
            if teacher_course_name:
                try:
                    assignments = parse_teacher_course_lines(teacher_course_name)
                    cleaned_data['teacher_course_assignments'] = assignments
                    cleaned_data['teacher_course_name'] = format_teacher_course_lines(assignments)

                except forms.ValidationError as exc:
                    self.add_error('teacher_course_name', exc)
            else:
                cleaned_data['teacher_course_assignments'] = []
        else:
            cleaned_data['teacher_course_name'] = ''
            cleaned_data['teacher_course_assignments'] = []

        club_positions = {}

        if is_club_member:
            if not club_names:
                self.add_error('club_names', 'Please select at least one club.')

            for club_name in club_names:
                position_field_name = club_position_field_name(club_name)
                position = cleaned_data.get(position_field_name)

                if not position:
                    club_label = dict(User.CLUB_CHOICES).get(club_name, club_name)
                    self.add_error(
                        position_field_name,
                        f'Please select your position for {club_label}.'
                    )
                else:
                    club_positions[club_name] = position
        else:
            cleaned_data['club_names'] = []

        cleaned_data['club_positions'] = club_positions

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        teacher_assignments = self.cleaned_data.get('teacher_course_assignments', [])
        user.teacher_course_name = teacher_assignments[0][1] if teacher_assignments else ''

        club_names = self.cleaned_data.get('club_names', [])
        club_positions = self.cleaned_data.get('club_positions', {})

        user.club_name = club_names[0] if club_names else ''
        user.club_position = club_positions.get(user.club_name, '') if user.club_name else ''

        if commit:
            existing_memberships = {
                membership.club_name: {
                    'is_verified': membership.is_verified,
                    'authorized_to_post': membership.authorized_to_post,
                }
                for membership in ClubMembership.objects.filter(user=user)
            }

            user.save()

            if user.is_teacher():
                TeacherCourseAssignment.objects.filter(teacher=user).delete()

                for semester, course_name in teacher_assignments:
                    TeacherCourseAssignment.objects.create(
                        teacher=user,
                        semester=semester,
                        course_name=course_name
                    )

            if user.is_club_member:
                ClubMembership.objects.filter(user=user).delete()

                for club_name in club_names:
                    old_data = existing_memberships.get(club_name, {})

                    ClubMembership.objects.create(
                        user=user,
                        club_name=club_name,
                        club_position=club_positions.get(club_name, ''),
                        is_verified=old_data.get('is_verified', False),
                        authorized_to_post=old_data.get('authorized_to_post', True)
                    )
            else:
                ClubMembership.objects.filter(user=user).delete()

        return user