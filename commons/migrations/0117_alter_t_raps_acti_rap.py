# Generated by Django 5.2 on 2025-05-20 00:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0116_t_raps_ficha_fase'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_raps_acti',
            name='rap',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_raps_ficha'),
        ),
    ]
