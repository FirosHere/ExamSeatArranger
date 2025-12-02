# forms.py
from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'department', 'student_class', 'academic_year']

class UploadCSVForm(forms.Form):
    file = forms.FileField()
