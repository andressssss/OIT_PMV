from django import forms
from django.contrib.auth.models import User
from commons.models import T_oferta

class OfertaCreateForm(forms.ModelForm):
    class Meta:
        model = T_oferta
        exclude = ['esta', 'usu_cre']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_contra': forms.Select(attrs={'class': 'form-select'}),
            'jorna_labo': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descri': forms.Textarea(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),  
            'fecha_ape': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_cie': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date'}),
            'edu_mini': forms.TextInput(attrs={'class': 'form-select'}), 
            'expe_mini': forms.TextInput(attrs={'class': 'form-select'}),  
            'profe_reque': forms.TextInput(attrs={'class': 'form-select'}),  
            'depa': forms.Select(attrs={'class': 'form-select'}),
            'progra': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nom': 'Nombre de la oferta',
            'tipo_contra': 'Tipo de contrato',
            'jorna_labo': 'Jornada laboral',
            'tipo': 'Tipo de contrato',
            'descri': 'Descripcion de la oferta',
            'cargo': 'Cargo',
            'fecha_ape': 'Fecha de apertura',
            'fecha_cie': 'Fecha de cierre',
            'edu_mini': 'Educacion minima',
            'expe_mini': 'Experiencia minima',
            'profe_reque': 'Profesion requerida',
            'depa': 'Departamento',
            'progra': 'Programa de formacion asociado',
        }
