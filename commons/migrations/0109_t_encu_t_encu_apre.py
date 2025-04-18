# Generated by Django 5.1.4 on 2025-04-11 12:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0108_remove_t_encu_apre_encu_remove_t_encu_apre_apre_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='T_encu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(blank=True, null=True)),
                ('tema', models.CharField(max_length=200)),
                ('fase', models.CharField(choices=[('fase analisis', 'Fase Analisis'), ('fase planeacion', 'Fase Planeacion'), ('fase ejecucion', 'Fase Ejecucion'), ('fase evaluacion', 'Fase Evaluacion')], max_length=200)),
                ('lugar', models.CharField(max_length=200)),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_ficha')),
                ('guia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_guia')),
            ],
            options={
                'db_table': 't_encu',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='T_encu_apre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prese', models.CharField(max_length=200)),
                ('apre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_apre')),
                ('encu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_encu')),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_ficha')),
            ],
            options={
                'db_table': 't_encu_apre',
                'managed': True,
            },
        ),
    ]
