# Generated by Django 5.1.4 on 2025-04-08 03:34

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0099_alter_t_fase_ficha_instru'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_crono',
            name='fecha_fin_acti',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='t_crono',
            name='fecha_fin_cali',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='t_crono',
            name='fecha_ini_acti',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='t_crono',
            name='fecha_ini_cali',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
