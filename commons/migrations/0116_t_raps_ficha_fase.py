# Generated by Django 5.2 on 2025-05-18 01:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0115_alter_t_crono_nove'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_raps_ficha',
            name='fase',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='commons.t_fase'),
            preserve_default=False,
        ),
    ]
