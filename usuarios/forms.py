from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from commons.models import T_gestor_depa,T_docu_labo, T_instru, T_perfil,T_gestor, T_nove, T_admin, T_apre, T_lider, T_repre_legal, T_munici, T_departa, T_insti_edu, T_centro_forma

class UserFormEdit(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        exclude = ['password']
        widgets = {

            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el mail'}),
        }
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }
        help_texts = {

            'username': None
        }

class UserFormCreate(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el nombre de usuario'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Escriba la contraseña de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el mail'}),
        }
        labels = {
            'username': 'Nombre de usuario',
            'password': 'Contraseña',
            'email': 'Correo electrónico',
        }
        help_texts = {
            'username': None,
            'password': None
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control w-50 mx-auto', 'placeholder': 'Contraseña actual'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control w-50 mx-auto', 'placeholder': 'Nueva contraseña'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control w-50 mx-auto', 'placeholder': 'Confirmar nueva contraseña'})

class DocumentoLaboralForm(forms.ModelForm):
    documento = forms.FileField(
        required=True,
        label="Documento",
        widget=forms.FileInput(attrs={'class': 'form-control'})  # Aquí se agregan los atributos correctamente
    )

    class Meta:
        model = T_docu_labo
        fields = ['nom', 'cate', 'documento']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'cate': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Institución',
            'cate': 'Categoría',
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = T_perfil
        exclude = ['user', 'rol']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'apelli': forms.TextInput(attrs={'class': 'form-control'}),
            'mail': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo_dni': forms.Select(attrs={'class': 'form-select'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'tele': forms.NumberInput(attrs={'class': 'form-control'}),
            'dire': forms.TextInput(attrs={'class': 'form-control'}),
            'gene': forms.Select(attrs={'class': 'form-select'}),
            'fecha_naci': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'nom': 'Nombres',
            'apelli': 'Apellidos',
            'mail': 'Correo electrónico',
            'tipo_dni': 'Tipo de documento',
            'dni': 'Número de documento',
            'tele': 'Teléfono',
            'dire': 'Dirección',
            'gene': 'Género',
            'fecha_naci': 'Fecha de nacimiento'
        }

class PerfilEForm(forms.ModelForm):
    class Meta:
        model = T_perfil
        exclude = ['user', 'rol', 'mail']  # Excluir los campos que no serán editables directamente
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apelli': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'tipo_dni': forms.Select(attrs={'class': 'form-select'}),
            'dni': forms.NumberInput(attrs={'class': 'form-control'}),
            'tele': forms.NumberInput(attrs={'class': 'form-control'}),
            'dire': forms.TextInput(attrs={'class': 'form-control'}),
            'gene': forms.Select(attrs={'class': 'form-select'}),
            'fecha_naci': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'nom': 'Nombres',
            'apelli': 'Apellidos',
            'tipo_dni': 'Tipo de documento',
            'dni': 'Número de documento',
            'tele': 'Teléfono',
            'dire': 'Dirección',
            'gene': 'Género',
            'fecha_naci': 'Fecha de nacimiento'
        }

    def save(self, commit=True):
        perfil = super().save(commit=False)  # Guardar el perfil sin comprometer los datos todavía

        # Actualizar el usuario relacionado
        user = perfil.user
        user.first_name = perfil.nom  # Actualizar el nombre en auth_user
        user.last_name = perfil.apelli  # Actualizar el apellido en auth_user
        user.email = perfil.mail  # Si mail está excluido, asegúrate de manejarlo en algún lugar

        if commit:
            user.save()  # Guardar cambios en auth_user
            perfil.save()  # Guardar cambios en T_perfil

        return perfil
    
class PerfilEditForm(forms.ModelForm):
    class Meta:
        model = T_perfil
        exclude = ['user', 'rol', 'mail', 'fecha_naci', 'gene']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apelli': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'tipo_dni': forms.Select(attrs={'class': 'form-select'}),
            'dni': forms.NumberInput(attrs={'class': 'form-control'}),
            'tele': forms.NumberInput(attrs={'class': 'form-control'}),
            'dire': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nombres',
            'apelli': 'Apellidos',
            'tipo_dni': 'Tipo de documento',
            'dni': 'Número de documento',
            'tele': 'Teléfono',
            'dire': 'Dirección',
        }

class InstructorForm(forms.ModelForm):
    class Meta:
        model = T_instru
        exclude = ['perfil', 'esta']  # El perfil se asignará automáticamente
        widgets = {
            'contra': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_ini': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profe': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_vincu': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'contra': 'Número de contrato',
            'fecha_ini': 'Fecha de inicio',
            'fecha_fin': 'Fecha de finalización',
            'profe': 'Profesión',
            'tipo_vincu': 'Tipo de vinculación'
        }

class AprendizForm(forms.ModelForm):
    class Meta:
        model = T_apre
        exclude = ['perfil', 'ficha', 'grupo', 'repre_legal']
        widgets = {
            'cod': forms.TextInput(attrs={'class': 'form-control'}),
            'esta': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cod': 'Código',
            'esta':  'Estado',
        }

class RepresanteLegalForm(forms.ModelForm):
    class Meta:
        model = T_repre_legal
        fields = ['nom','dni', 'tele', 'dire', 'mail', 'paren']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'tele': forms.TextInput(attrs={'class': 'form-control'}),
            'dire': forms.TextInput(attrs={'class': 'form-control'}),
            'mail': forms.EmailInput(attrs={'class': 'form-control'}),
            'paren': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'nom': 'Nombre',
            'dni': 'Número de identificación',
            'tele': 'Teléfono',
            'dire': 'Dirección',
            'mail': 'Correo',
            'paren': 'Parentesco'
        }

class NovedadForm(forms.ModelForm):
    class Meta:
        model = T_nove
        exclude = ['estado']  # El estado se asignara automaticamente
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descri': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'sub_tipo': forms.Select(attrs={'class': 'form-select'})
        }
        labels = {
            'nombre': 'Nombre',
            'descri': 'Descripción',
            'tipo': 'Tipo',
            'sub_tipo': 'Sub Tipo'
        }

class AdministradoresForm(forms.ModelForm):
    class Meta:
        model = T_admin
        exclude = ['perfil', 'esta']
        field = ['area']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'area': 'Area',
        }

class LiderForm(forms.ModelForm):
    class Meta:
        model = T_lider
        exclude = ['perfil']
        widgets = {
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'esta': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'area': 'Area',
            'esta':  'Estado'
        }

class GestorForm(forms.ModelForm):
    class Meta:
        model = T_gestor
        exclude = ['perfil']
        widgets = {
            'esta': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'esta':  'Estado'
        }

class GestorDepaForm(forms.Form):
    departamentos = forms.ModelMultipleChoiceField(
        queryset=T_departa.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )

class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = T_departa
        fields = ['cod_departa', 'nom_departa']
        widgets = {
            'cod_departa': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_departa': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'cod_departa': 'Código de departamento',
            'nom_departa': 'Departamento',
        }

class MunicipioForm(forms.ModelForm):
    class Meta:
        model = T_munici
        fields = ['cod_munici', 'nom_munici', 'nom_departa']
        widgets = {
            'cod_munici': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_munici': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_departa': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cod_munici': 'Código de municipio',
            'nom_munici': 'Municipio',
            'nom_departa': 'Departamento',
        }

class InstitucionForm(forms.ModelForm):
    depa = forms.ModelChoiceField(
        queryset= T_departa.objects.all(),
        empty_label="Seleccione un departamento",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_depa'}),
        required=False
    )
    class Meta:
        model = T_insti_edu
        fields = ['depa', 'nom', 'dire', 'secto', 'muni', 'coordi', 'coordi_mail', 'coordi_tele', 'esta', 'insti_mail', 'dane', 'recto', 'recto_tel',  'gene', 'grados', 'jorna', 'num_sedes', 'zona', 'cale']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'dire': forms.TextInput(attrs={'class': 'form-control'}),
            'secto': forms.Select(attrs={'class': 'form-control'}),
            'muni': forms.Select(attrs={'class': 'form-control', 'id': 'muni', }, choices=[("", "Seleccione un municipio")]),
            'coordi': forms.TextInput(attrs={
                'class': 'form-control',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'title': 'Nombre de la persona encargada del convenio'
                }),
            'coordi_mail': forms.TextInput(attrs={
                'class': 'form-control',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'title': 'Correo de la persona encargada del convenio'
                }),
            'coordi_tele': forms.TextInput(attrs={
                'class': 'form-control',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'title': 'Teléfono de la persona encargada del convenio'
                }),
            'esta': forms.Select(attrs={'class': 'form-control'}),
            'insti_mail': forms.TextInput(attrs={'class': 'form-control'}),
            'dane': forms.TextInput(attrs={'class': 'form-control'}),
            'recto': forms.TextInput(attrs={'class': 'form-control'}),
            'recto_tel': forms.TextInput(attrs={'class': 'form-control'}),
            'gene': forms.Select(attrs={'class': 'form-control'}),
            'grados': forms.TextInput(attrs={'class': 'form-control'}),
            'jorna': forms.TextInput(attrs={'class': 'form-control'}),
            'num_sedes': forms.TextInput(attrs={'class': 'form-control'}),
            'zona': forms.Select(attrs={'class': 'form-control'}),
            'vigen': forms.TextInput(attrs={'class': 'form-control'}),
            'cale': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'nom': 'Nombre institución',
            'dire': 'Dirección institución',
            'secto': 'Sector',
            'muni': 'municipio',
            'coordi': 'Coordinador',
            'coordi_mail': 'Correo coordinador',
            'coordi_tele': 'Teléfono coordinador',
            'esta': 'Estado',
            'insti_mail': 'Correo institución',
            'dane': 'Código DANE',
            'recto': 'Nombre Rector',
            'recto_tel': 'Teléfono rector',
            'gene': 'Genero',
            'grados': 'Grados',
            'jorna': 'Jornada',
            'num_sedes': 'Número de sedes',
            'zona': 'Zona',
            'vigen': 'Vigencia',
            'cale': 'Calendario',
            'depa': 'Departamento'
        }

class CentroFormacionForm(forms.ModelForm):
    class Meta:
        model = T_centro_forma
        fields = ['nom', 'depa', 'cod']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'depa': forms.Select(attrs={'class': 'form-control select2'}),
            'cod': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nombre de centro de formación',
            'depa': 'Departamento del centro de formación',
            'cod': 'Código del centro de formación',
        }

class CargarAprendicesMasivoForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label="Seleccione un archivo CSV"
    )