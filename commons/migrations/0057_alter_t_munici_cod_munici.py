# Generated by Django 5.1.4 on 2025-01-11 02:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0056_t_nove_ficha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_munici',
            name='cod_munici',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
