# Generated by Django 5.1.4 on 2024-12-24 23:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0032_remove_t_documentfolder_ficha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_documentfolder',
            name='ficha',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='commons.t_ficha'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_documentfolder',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='T_DocumentContent',
        ),
    ]
