# Generated by Django 5.1.4 on 2024-12-20 03:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0008_rename_t_perfi_t_perfil_rename_nombre_t_perfil_nom_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='t_acti_ficha',
            name='instru',
        ),
        migrations.AddField(
            model_name='t_ficha',
            name='instru',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='commons.t_instru'),
            preserve_default=False,
        ),
    ]
