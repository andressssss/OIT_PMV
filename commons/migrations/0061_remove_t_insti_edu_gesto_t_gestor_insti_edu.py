# Generated by Django 5.1.4 on 2025-01-12 00:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0060_alter_t_perfil_rol_t_gestor_t_insti_edu_gesto'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='t_insti_edu',
            name='gesto',
        ),
        migrations.CreateModel(
            name='T_gestor_insti_edu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_regi', models.DateTimeField(blank=True, null=True)),
                ('esta', models.CharField(max_length=10)),
                ('año', models.CharField(max_length=10)),
                ('seme', models.CharField(max_length=2)),
                ('gestor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_gestor')),
                ('insti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_insti_edu')),
                ('usuario_asigna', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'T_gestor_insti_edu',
                'managed': True,
            },
        ),
    ]