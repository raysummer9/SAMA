from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Course, Attendance, FacultyUser, AttendanceSession

class FacultyLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = FacultyUser.objects.get(email=email)
                if not user.check_password(password):
                    raise forms.ValidationError('Invalid email or password.')
            except FacultyUser.DoesNotExist:
                raise forms.ValidationError('Invalid email or password.')
        return cleaned_data

class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['course', 'date', 'start_time', 'end_time', 'grace_period']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'grace_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'placeholder': 'Enter grace period in minutes'
            }),
        }

    def __init__(self, *args, **kwargs):
        faculty = kwargs.pop('faculty', None)
        super().__init__(*args, **kwargs)
        if faculty:
            self.fields['course'].queryset = Course.objects.filter(faculty=faculty)

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'matric_number', 'email']
        labels = {
            'matric_number': 'Matric Number',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'matric_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'course', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 