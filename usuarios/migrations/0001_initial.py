# Generated by Django 5.1.4 on 2024-12-12 13:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='T_perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('apelli', models.CharField(max_length=200)),
                ('dni', models.IntegerField(choices=[('ti', 'Tarjeta de identidad'), ('cc', 'Cedula de ciudadania'), ('pp', 'Pasaporte'), ('cc', 'Tarjeta de extranjeria')], max_length=50)),
                ('tele', models.IntegerField(max_length=50)),
                ('dire', models.CharField(max_length=200)),
                ('mail', models.EmailField(max_length=200)),
                ('gene', models.CharField(choices=[('H', 'Hombre'), ('M', 'Mujer')], max_length=20)),
                ('fecha_naci', models.DateField(blank=True, null=True)),
                ('rol', models.CharField(choices=[('admin', 'Admin'), ('instructor', 'Instructor'), ('aprendiz', 'Aprendiz'), ('lider', 'Lider')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='T_instructor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contra', models.CharField(max_length=200)),
                ('fecha_ini', models.DateField(blank=True, null=True)),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('esta', models.CharField(max_length=200)),
                ('profe', models.CharField(max_length=200)),
                ('tipo_vincu', models.CharField(choices=[('termino indefinido', 'Termino indefinido'), ('colaborador externo', 'Colaborador externo')], max_length=50)),
                ('perfil', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='usuarios.t_perfil')),
            ],
        ),
    ]
