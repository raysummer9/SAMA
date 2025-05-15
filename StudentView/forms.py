from django import forms
from FacultyView.models import Student

class StudentLoginForm(forms.Form):
    matric_number = forms.CharField(
        label='Matric Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your matric number'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        matric_number = cleaned_data.get('matric_number')

        if matric_number:
            try:
                student = Student.objects.get(matric_number=matric_number)
                cleaned_data['student'] = student
            except Student.DoesNotExist:
                raise forms.ValidationError('Invalid matric number.')
        return cleaned_data 