# Generated by Django 5.1.4 on 2024-12-20 00:29

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0004_remove_t_documentos_ruta_t_documentos_archi_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='T_perfil',
            new_name='T_perfi',
        ),
        migrations.AlterModelOptions(
            name='t_perfi',
            options={'managed': True},
        ),
        migrations.AlterModelTable(
            name='t_perfi',
            table='T_perfi',
        ),
    ]
