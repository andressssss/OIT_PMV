# Generated by Django 5.1.4 on 2025-01-12 12:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0062_alter_t_gestor_esta_t_grupo_t_gestor_grupo_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='t_gestor_insti_edu',
            old_name='año',
            new_name='ano',
        ),
    ]
