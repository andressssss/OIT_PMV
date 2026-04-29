from django.contrib import admin
from django import forms

from commons.models import T_perfil
from tasks.models import T_notifi, T_alerta_regla


@admin.register(T_notifi)
class TNotifiAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'nivel', 'titulo', 'leida', 'creada_en')
    list_filter = ('nivel', 'leida', 'origen_tipo')
    search_fields = ('titulo', 'mensaje', 'usuario__username')
    readonly_fields = ('creada_en', 'leida_en')


ROLES_DESTINATARIOS = ('admin', 'lider', 'gestor', 'cuentas', 'consulta')


class TAlertaReglaForm(forms.ModelForm):
    class Meta:
        model = T_alerta_regla
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'destinatarios' in self.fields:
            qs = T_perfil.objects.filter(rol__in=ROLES_DESTINATARIOS).order_by('nom', 'apelli')
            self.fields['destinatarios'].queryset = qs
            self.fields['destinatarios'].label_from_instance = (
                lambda p: f"{p.nom} {p.apelli} - {p.dni} ({p.get_rol_display()})"
            )


@admin.register(T_alerta_regla)
class TAlertaReglaAdmin(admin.ModelAdmin):
    form = TAlertaReglaForm
    list_display = (
        'tipo', 'nivel', 'activa', 'dias_umbral',
        'enviar_correo', 'enviar_notificacion', 'destinatarios_count',
    )
    list_filter = ('activa', 'nivel', 'tipo')
    filter_horizontal = ('destinatarios',)
    readonly_fields = ('creada_en', 'actualizada_en')
    fieldsets = (
        (None, {
            'fields': ('tipo', 'nivel', 'activa', 'dias_umbral'),
        }),
        ('Destinatarios', {
            'fields': ('destinatarios', 'incluir_instructor_ficha'),
        }),
        ('Canales', {
            'fields': ('enviar_correo', 'enviar_notificacion'),
        }),
        ('Plantillas', {
            'fields': ('asunto_correo', 'plantilla_mensaje'),
        }),
        ('Otros', {
            'fields': ('notas', 'creada_en', 'actualizada_en'),
        }),
    )

    @admin.display(description='# Destinatarios')
    def destinatarios_count(self, obj):
        return obj.destinatarios.count()
