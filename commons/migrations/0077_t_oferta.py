# Generated by Django 5.1.4 on 2025-01-16 18:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0076_rename_estado_t_cuentas_esta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='T_oferta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('tipo_contra', models.CharField(choices=[('terminoi', 'Termino Indefinido'), ('prestacion', 'Prestacion de servicios'), ('obra', 'Obra labor'), ('fijo', 'Termino fijo')], max_length=200)),
                ('jorna_labo', models.CharField(choices=[('tiempoc', 'Tiempo completo'), ('horas', 'Por horas'), ('parcial', 'Tiempo parcial')], max_length=100)),
                ('tipo', models.CharField(choices=[('presencial', 'Presencial'), ('virtual', 'Virtual'), ('hibrido', 'Hibrido')], max_length=50)),
                ('decri', models.TextField(max_length=3000)),
                ('cargo', models.CharField(max_length=200)),
                ('esta', models.CharField(choices=[('creado', 'Creado'), ('publicado', 'Publicado'), ('cerrado', 'Cerrado')], max_length=50)),
                ('fecha_crea', models.DateTimeField(auto_now_add=True)),
                ('fecha_ape', models.DateTimeField()),
                ('fecha_cie', models.DateTimeField()),
                ('edu_mini', models.CharField(max_length=200)),
                ('expe_mini', models.CharField(max_length=200)),
                ('profe_reque', models.CharField(max_length=100)),
                ('depa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_departa')),
                ('progra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_progra')),
                ('usu_cre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'T_oferta',
                'managed': True,
            },
        ),
    ]
