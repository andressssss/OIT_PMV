# Generated by Django 5.1.4 on 2024-12-18 14:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0002_t_fichas_num'),
    ]

    operations = [
        migrations.CreateModel(
            name='T_subtipo_novedad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_tipo_novedad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='t_novedades',
            name='descri',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='t_novedades',
            name='estado',
            field=models.CharField(choices=[('creado', 'Creado'), ('gestion', 'En gestion'), ('resuelto', 'Resuelto')], max_length=200),
        ),
        migrations.AddField(
            model_name='t_novedades',
            name='sub_tipo',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='commons.t_subtipo_novedad'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_subtipo_novedad',
            name='tipo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtipos', to='commons.t_tipo_novedad'),
        ),
        migrations.AlterField(
            model_name='t_novedades',
            name='tipo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='commons.t_tipo_novedad'),
        ),
    ]
