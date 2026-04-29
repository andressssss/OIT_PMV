from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_tasks_datecompleted'),
        ('commons', '0156_t_consulta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='T_notifi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField(blank=True)),
                ('nivel', models.CharField(
                    choices=[('info', 'Información'), ('preventiva', 'Preventiva'),
                             ('seguimiento', 'Seguimiento'), ('riesgo', 'Riesgo')],
                    default='info', max_length=20)),
                ('url', models.CharField(blank=True, max_length=500, null=True)),
                ('leida', models.BooleanField(default=False)),
                ('leida_en', models.DateTimeField(blank=True, null=True)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('origen_tipo', models.CharField(blank=True, max_length=50, null=True)),
                ('origen_id', models.IntegerField(blank=True, null=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name='notificaciones',
                                               to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 't_notifi',
                'ordering': ['-creada_en'],
            },
        ),
        migrations.AddIndex(
            model_name='t_notifi',
            index=models.Index(fields=['usuario', 'leida'], name='t_notifi_usuario_leida_idx'),
        ),
        migrations.AddIndex(
            model_name='t_notifi',
            index=models.Index(fields=['origen_tipo', 'origen_id'], name='t_notifi_origen_idx'),
        ),
        migrations.CreateModel(
            name='T_alerta_regla',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('inactividad_preventiva', 'Inactividad - Preventiva'),
                             ('inactividad_seguimiento', 'Inactividad - Seguimiento'),
                             ('mayoria_edad_preventiva', 'Mayoría de edad - 30 días antes'),
                             ('mayoria_edad_dia0', 'Mayoría de edad - Día del cumpleaños'),
                             ('mayoria_edad_riesgo', 'Mayoría de edad - Riesgo (CC sin actualizar)')],
                    max_length=50, unique=True)),
                ('nivel', models.CharField(
                    choices=[('info', 'Información'), ('preventiva', 'Preventiva'),
                             ('seguimiento', 'Seguimiento'), ('riesgo', 'Riesgo')],
                    default='preventiva', max_length=20)),
                ('activa', models.BooleanField(default=True)),
                ('dias_umbral', models.IntegerField(
                    help_text='Días para activar la regla (positivo o negativo según el tipo)')),
                ('incluir_instructor_ficha', models.BooleanField(
                    default=False,
                    help_text='Si está activo, también notifica al instructor de la ficha del aprendiz (sólo aplica a reglas de mayoría de edad)')),
                ('enviar_correo', models.BooleanField(default=True)),
                ('enviar_notificacion', models.BooleanField(default=True)),
                ('asunto_correo', models.CharField(
                    blank=True, max_length=200,
                    help_text='Plantilla. Variables disponibles: {nombre}, {dni}, {dias}')),
                ('plantilla_mensaje', models.TextField(
                    blank=True,
                    help_text='Plantilla del cuerpo. Variables: {nombre}, {dni}, {dias}, {url}')),
                ('notas', models.TextField(blank=True)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('actualizada_en', models.DateTimeField(auto_now=True)),
                ('destinatarios', models.ManyToManyField(
                    blank=True, related_name='alertas_destino', to='commons.t_perfil',
                    help_text='Perfiles que reciben la notificación/correo (admin, líder, gestor, etc.)')),
            ],
            options={
                'verbose_name': 'Regla de alerta',
                'verbose_name_plural': 'Reglas de alerta',
                'db_table': 't_alerta_regla',
            },
        ),
    ]
