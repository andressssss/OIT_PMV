# Generated by Django 5.1.4 on 2024-12-20 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0013_t_acti_fase'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_acti',
            name='descri',
            field=models.CharField(default=1, max_length=500),
            preserve_default=False,
        ),
    ]
