from django import forms
from commons.models import T_fase, T_centro_forma, T_docu,T_departa, T_insti_edu, T_munici, T_encu,T_apre, T_progra, T_compe, T_raps, T_ficha
import logging

logger = logging.getLogger(__name__)


class FichaForm(forms.ModelForm):
    class Meta:
        model = T_ficha
        fields = [ 'num_apre_proce', 'progra']
        widgets = {
            'num_apre_proce': forms.TextInput(attrs={'class': 'form-control'}), 
            'progra': forms.Select(attrs={'class': 'form-select'})
        }
        labels = {
            'num_apre_proce': 'Numero de aprendices en proceso', 
            'progra': 'Programa de formacion'
        }

class CascadaMunicipioInstitucionForm(forms.Form):
    departamento = forms.ModelChoiceField(
        queryset=T_departa.objects.all(),
        required=False,
        empty_label="Selecciona un departamento",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'})
    )
    municipio = forms.ModelChoiceField(
        queryset=T_munici.objects.none(),
        required=False,
        empty_label="Selecciona un municipio",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_municipio'})
    )
    centro = forms.ModelChoiceField(
        queryset=T_centro_forma.objects.none(),
        required=False,
        empty_label="Selecciona un centro",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_centro'})
    )
    insti = forms.ModelChoiceField(
        queryset=T_insti_edu.objects.none(),
        required=False,
        empty_label="Selecciona una institución",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_insti'})
    )


class DocumentosForm(forms.ModelForm):
    class Meta:
        model = T_docu
        exclude = ['nom', 'tipo', 'tama', 'priva', 'esta']
        widgets = {
            'archi': forms.FileInput(attrs={'class': 'form-select'})
        }
        labels = {
            'archi': 'Archivo'
        }


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = T_progra
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'label': 'Ingrese el nombre del programa'})
        }
        labels = {
            'nom': 'Nombre del programa'
        }

class CompetenciaForm(forms.ModelForm):
    class Meta:
        model = T_compe
        fields = ['nom', 'progra']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la competencia'
            }),
            'progra': forms.SelectMultiple(attrs={
                'class': 'form-control tomselect,',
                'data-placeholder': 'Seleccione uno o varios programas'
            })
        }
        labels = {
            'nom': 'Nombre',
            'progra': 'Programas'
        }

class RapsForm(forms.ModelForm):
    fase = forms.ModelMultipleChoiceField(
        queryset=T_fase.objects.all(),
        required=True,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control tomselectm',
            'data-placeholder': 'Seleccione una o varias fases'
        }),
        label="Fases"
    )

    class Meta:
        model = T_raps
        exclude = ['comple']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'compe': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nombre',
            'compe': 'Competencia',
        }


class EncuentroForm(forms.ModelForm):
    class Meta:
        model = T_encu
        fields = ['tema', 'lugar', 'fecha']
        widgets = {
            'tema': forms.TextInput(attrs={'class': 'form-control'}),
            'lugar': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }
        labels = {
            'tema': 'Tema del encuentro',
            'lugar': 'Lugar de encuentro',
            'fecha': 'Fecha del encuentro'
        }

class EncuApreForm(forms.Form):
    aprendices = forms.ModelMultipleChoiceField(
        queryset=T_apre.objects.none(),  # Inicialmente vacío
        widget=forms.CheckboxSelectMultiple,  # Widget de checkboxes
        required=False  # No es obligatorio seleccionar RAPs
    )

    def __init__(self, *args, **kwargs):
        ficha = kwargs.pop('ficha', None)  # Extraer 'ficha' de los argumentos
        super().__init__(*args, **kwargs)  # Llamar al constructor de la clase base
        if ficha:
            # Si se pasó una ficha, ajustar el queryset para incluir los RAPs de la ficha
            self.fields['aprendices'].queryset = T_apre.objects.filter(ficha=ficha)

class CargarDocuPortafolioFichaForm(forms.Form):
    nombre_documento = forms.CharField(max_length=255, label="Nombre del Documento")
    url_documento = forms.URLField(label="URL del Documento")


class CargarFichasMasivoForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label="Seleccione un archivo CSV"
    )