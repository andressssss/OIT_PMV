# Generated by Django 5.1.4 on 2024-12-20 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0015_t_raps_comple_t_raps_fase_t_rap_acti'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_raps',
            name='fase',
            field=models.CharField(choices=[('fase analisis', 'Fase Analisis'), ('fase planeacion', 'Fase Planeacion'), ('fase ejecucion', 'Fase Ejecucion'), ('fase evaluacion', 'Fase Evaluacion')], max_length=100),
        ),
    ]
