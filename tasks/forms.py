from django import forms
from .models import tasks

class TaskForm(forms.ModelForm):
    class Meta:
        model = tasks
        fields = ['title', 'description', 'important']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba un titulo'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escriba la descripcion'}),
            'important': forms.CheckboxInput(attrs={'class': 'form-check-button m-auto'})
        }