from django import forms
from django_select2 import forms as s2forms
from commons.models import T_apre, T_grupo,T_gestor_insti_edu, T_insti_edu, T_munici, T_departa,T_perfil, T_gestor, T_centro_forma, T_gestor_depa
from django.core.exceptions import ObjectDoesNotExist

class AsignarAprendicesGrupoForm(forms.Form):
    aprendices = forms.ModelMultipleChoiceField(
        queryset=T_apre.objects.filter(grupo__isnull=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )

# class GrupoForm(forms.ModelForm):
#     departamento = forms.ModelChoiceField(
#         queryset=T_departa.objects.all(),
#         required=False,
#         label="Departamento",
#         widget=forms.Select(attrs={'class': 'form-select'}),
#     )
#     municipio = forms.ModelChoiceField(
#         queryset=T_munici.objects.none(),
#         required=False,
#         label="Municipio",
#         widget=forms.Select(attrs={'class': 'form-select'}),
#     )
#     centro = forms.ModelChoiceField(
#         queryset=T_centro_forma.objects.none(),
#         required=False,
#         label="Centro de Formación",
#         widget=forms.Select(attrs={'class': 'form-select'}),
#     )
#     insti = forms.ModelChoiceField(
#         queryset=T_insti_edu.objects.none(),
#         label="Institución Educativa",
#         widget=forms.Select(attrs={'class': 'form-select'}),
#     )

#     class Meta:
#         model = T_grupo
#         fields = ['num_apre_poten', 'departamento', 'municipio', 'centro', 'insti']
#         widgets = {
#             'num_apre_poten': forms.TextInput(attrs={'class': 'form-control'}),
#         }
#         labels = {
#             'num_apre_poten': 'Aprendices potenciales',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Filtrar municipios según el departamento seleccionado
#         if 'departamento' in self.data:
#             try:
#                 departamento_id = int(self.data.get('departamento'))
#                 self.fields['municipio'].queryset = T_munici.objects.filter(nom_departa_id=departamento_id)
#                 self.fields['centro'].queryset = T_centro_forma.objects.filter(depa_id=departamento_id)
#             except (ValueError, TypeError):
#                 pass

#         # Filtrar instituciones educativas según el municipio seleccionado
#         if 'municipio' in self.data:
#             try:
#                 municipio_id = int(self.data.get('municipio'))
#                 self.fields['insti'].queryset = T_insti_edu.objects.filter(muni_id=municipio_id)
#             except (ValueError, TypeError):
#                 pass

#         # Establecer valores por defecto si hay una instancia existente
#         if self.instance.pk:
#             self.fields['municipio'].queryset = self.instance.departamento.t_munici_set.all()
#             self.fields['centro'].queryset = self.instance.departamento.t_centro_forma_set.all()
#             self.fields['insti'].queryset = self.instance.municipio.t_insti_edu_set.all()

class GrupoForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        required=True,
        label="Centro de Formación",
        queryset=T_centro_forma.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    insti = forms.ModelChoiceField(
        queryset=T_insti_edu.objects.none(),
        required=True,
        label="Institución Educativa",
        widget=forms.Select(attrs={'class': 'form-control select2'}),
    )

    class Meta:
        model = T_grupo
        fields = ['num_apre_poten', 'centro', 'insti', 'progra']
        widgets = {
            'num_apre_poten': forms.TextInput(attrs={'class': 'form-control'}),
            'progra': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'num_apre_poten': 'Aprendices potenciales',
            'progra': 'Programa de formacion',
        }
    
    def __init__(self, *args, **kwargs):
        # Capturar el usuario desde los kwargs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar si el usuario está autenticado
        if user and user.is_authenticated:
            self.fields['insti'].queryset = T_insti_edu.objects.filter(
                id__in=T_gestor_insti_edu.objects.filter(usuario_asigna=user).values_list('insti_id', flat=True)
            )
            # perfil = getattr(user, 't_perfil', None)
            # if perfil:
            #     try:
            #         # Obtener el gestor asociado al perfil
            #         gestor = T_gestor.objects.get(perfil=perfil)

            #         # Filtrar T_departa a través de T_gestor_depa
            #         depas = T_departa.objects.filter(
            #             id__in=T_gestor_depa.objects.filter(gestor=gestor).values_list('depa_id', flat=True)
            #         )
            #         for depa in depas:
            #             print(depa.id)  
            #         centros = T_centro_forma.objects.filter(depa__in=depas.values_list('id', flat=True))
            #         for centro in centros:
            #             print(centro.nom)  
            #         # Filtrar T_centro_forma por los departamentos filtrados
            #         self.fields['centro'].queryset = T_centro_forma.objects.filter(depa__in=depas)


            #     except ObjectDoesNotExist:
            #         self.fields['centro'].queryset = T_centro_forma.objects.none()
            # else:
            #     self.fields['centro'].queryset = T_centro_forma.objects.none()
    def clean_num_apre_poten(self):
        num_apre_poten = self.cleaned_data.get('num_apre_poten')
        if not num_apre_poten.isdigit():
            raise forms.ValidationError("El numero de aprendices debe ser un numero")
        if int(num_apre_poten) <= 0:
            raise forms.ValidationError("El numero de aprendices debe ser mayor a 0")
        if int(num_apre_poten) < 1 or int(num_apre_poten) > 100:
            raise forms.ValidationError("El numero de aprendices debe estar entre 1 y 100")
        return num_apre_poten

class AsignarAprendicesMasivoForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label="Seleccione un archivo CSV"
    )

class AsignarInstiForm(forms.ModelForm):
    departamento = forms.ModelChoiceField(
        queryset=T_departa.objects.none(),
        required=False,
        label="Departamento",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    municipio = forms.ModelChoiceField(
        queryset=T_munici.objects.none(),
        required=False,
        label="Municipio",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    insti = forms.ModelChoiceField(
        queryset=T_insti_edu.objects.none(),
        label="Institución Educativa",
        widget=forms.Select(attrs={'class': 'form-select select2'}),
    )
    class Meta:
        model = T_gestor_insti_edu
        fields = [ 'departamento', 'municipio', 'insti']

    def __init__(self, *args, **kwargs):
        # Capturar el usuario desde los kwargs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar departamentos según el gestor
        if user and user.is_authenticated:
            perfil = T_perfil.objects.get(user=user.id)
            gestor = T_gestor.objects.get(perfil=perfil)
            self.fields['departamento'].queryset = T_departa.objects.filter(
                id__in=T_gestor_depa.objects.filter(gestor=gestor).values_list('depa_id', flat=True)
            )

            # Filtrar municipios según el departamento seleccionado
            if 'departamento' in self.data:
                try:
                    departamento_id = int(self.data.get('departamento'))
                    self.fields['municipio'].queryset = T_munici.objects.filter(nom_departa_id=departamento_id)
                except (ValueError, TypeError):
                    self.fields['municipio'].queryset = T_munici.objects.none()
            elif self.instance.pk:
                # Si hay una instancia, mostrar los municipios relacionados
                self.fields['municipio'].queryset = self.instance.departamento.t_munici_set.all()

            # Filtrar instituciones educativas según el municipio seleccionado
            if 'municipio' in self.data:
                try:
                    municipio_id = int(self.data.get('municipio'))
                    self.fields['insti'].queryset = T_insti_edu.objects.filter(muni_id=municipio_id)
                except (ValueError, TypeError):
                    self.fields['insti'].queryset = T_insti_edu.objects.none()
            elif self.instance.pk:
                # Si hay una instancia, mostrar las instituciones relacionadas
                self.fields['insti'].queryset = self.instance.municipio.t_insti_edu_set.all()
        else:
            # Si no hay un usuario autenticado, vaciar los campos
            self.fields['departamento'].queryset = T_departa.objects.none()
            self.fields['municipio'].queryset = T_munici.objects.none()
            self.fields['insti'].queryset = T_insti_edu.objects.none()