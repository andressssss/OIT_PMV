# Generated by Django 5.1.4 on 2025-03-28 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0094_alter_t_admin_area'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_perfil',
            name='tipo_dni',
            field=models.CharField(choices=[('ti', 'Tarjeta de identidad'), ('cc', 'Cedula de ciudadania'), ('pp', 'Pasaporte'), ('cc', 'Tarjeta de extranjeria')], max_length=50),
        ),
    ]
