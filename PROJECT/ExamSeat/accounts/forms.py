from django import forms
from .models import Student

# accounts/forms.py
from django import forms

from django import forms

class UploadCSVForm(forms.Form):
    file = forms.FileField()



class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['roll_number', 'name', 'department', 'student_class', 'academic_year']
