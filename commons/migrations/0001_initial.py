# Generated by Django 5.1.4 on 2024-12-18 01:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='T_actividades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('horas_auto', models.CharField(max_length=200)),
                ('horas_dire', models.CharField(max_length=200)),
                ('tipo', models.CharField(choices=[('conocimiento', 'Conocimiento'), ('desempeño', 'Desempeño'), ('producto', 'Producto')], max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='T_aprendiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cod', models.CharField(max_length=200)),
                ('esta', models.CharField(choices=[('activo', 'Activo'), ('suspendido', 'Suspendido'), ('prematricula', 'Pre matricula')], max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_centros_formacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('dire', models.CharField(max_length=100)),
                ('depa', models.CharField(max_length=100)),
                ('muni', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='T_cronogramas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nove', models.CharField(max_length=200)),
                ('fecha_ini_acti', models.DateTimeField(blank=True, null=True)),
                ('fecha_fin_acti', models.DateTimeField(blank=True, null=True)),
                ('fecha_ini_cali', models.DateTimeField(blank=True, null=True)),
                ('fecha_fin_cali', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='T_descriptores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_documentos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('tipo', models.CharField(max_length=200)),
                ('ruta', models.CharField(max_length=200)),
                ('tama', models.CharField(max_length=200)),
                ('priva', models.CharField(max_length=200)),
                ('esta', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_encuentros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(blank=True, null=True)),
                ('lugar', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_guias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('horas_auto', models.CharField(max_length=200)),
                ('horas_dire', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_instituciones_educativas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('dire', models.CharField(max_length=100)),
                ('ofi', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='T_instructor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contra', models.CharField(max_length=200)),
                ('fecha_ini', models.DateField(blank=True, null=True)),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('esta', models.CharField(max_length=200)),
                ('profe', models.CharField(max_length=200)),
                ('tipo_vincu', models.CharField(choices=[('termino indefinido', 'Termino indefinido'), ('colaborador externo', 'Colaborador externo')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='T_novedades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('tipo', models.CharField(max_length=200)),
                ('estado', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_programas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_recursos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_representante_legal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('tele', models.CharField(max_length=200)),
                ('dire', models.CharField(max_length=200)),
                ('mail', models.CharField(max_length=200)),
                ('paren', models.CharField(max_length=200)),
                ('ciu', models.CharField(max_length=200)),
                ('depa', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='T_actividades_documento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_actividades')),
                ('docu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_documentos')),
            ],
        ),
        migrations.CreateModel(
            name='T_actividades_ficha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('esta', models.CharField(max_length=200)),
                ('acti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_actividades')),
                ('crono', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_cronogramas')),
            ],
        ),
        migrations.CreateModel(
            name='T_actividades_aprendiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apro', models.CharField(max_length=200)),
                ('fecha', models.DateTimeField(blank=True, null=True)),
                ('acti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_actividades_ficha')),
                ('apre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_aprendiz')),
            ],
        ),
        migrations.CreateModel(
            name='T_actividades_descriptores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_actividades')),
                ('descri', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_descriptores')),
            ],
        ),
        migrations.CreateModel(
            name='T_documentos_proceso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('esta', models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], max_length=200)),
                ('autor', models.CharField(max_length=200)),
                ('publi', models.CharField(max_length=200)),
                ('docu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_documentos')),
            ],
        ),
        migrations.CreateModel(
            name='T_encuentros_aprendiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('encu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_encuentros')),
                ('estu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_aprendiz')),
            ],
        ),
        migrations.CreateModel(
            name='T_fichas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_aper', models.DateTimeField(blank=True, null=True)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('centro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_centros_formacion')),
                ('insti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_instituciones_educativas')),
            ],
        ),
        migrations.AddField(
            model_name='t_aprendiz',
            name='ficha',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_fichas'),
        ),
        migrations.AddField(
            model_name='t_actividades_ficha',
            name='ficha',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_fichas'),
        ),
        migrations.AddField(
            model_name='t_encuentros',
            name='guia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_guias'),
        ),
        migrations.CreateModel(
            name='T_criterios_evaluacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crite', models.CharField(max_length=200)),
                ('evi', models.CharField(max_length=200)),
                ('tecni', models.CharField(max_length=200)),
                ('guia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_guias')),
            ],
        ),
        migrations.CreateModel(
            name='T_guias_documento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_documentos')),
                ('guia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_guias')),
            ],
        ),
        migrations.CreateModel(
            name='T_fases_ficha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fase', models.CharField(choices=[('fase analisis', 'Fase Analisis'), ('fase planeacion', 'Fase Planeacion'), ('fase ejecucion', 'Fase Ejecucion'), ('fase evaluacion', 'Fase Evaluacion')], max_length=50)),
                ('fecha_ini', models.DateTimeField(blank=True, null=True)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_fichas')),
                ('instru', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_instructor')),
            ],
        ),
        migrations.AddField(
            model_name='t_actividades_ficha',
            name='instru',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_instructor'),
        ),
        migrations.CreateModel(
            name='T_novedades_documentos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_documentos')),
                ('nove', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_novedades')),
            ],
        ),
        migrations.CreateModel(
            name='T_novedades_ficha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_fichas')),
                ('nove', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_novedades')),
            ],
        ),
        migrations.CreateModel(
            name='T_perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('apelli', models.CharField(max_length=200)),
                ('tipo_dni', models.CharField(blank=True, choices=[('ti', 'Tarjeta de identidad'), ('cc', 'Cedula de ciudadania'), ('pp', 'Pasaporte'), ('cc', 'Tarjeta de extranjeria')], max_length=50)),
                ('dni', models.IntegerField()),
                ('tele', models.CharField(max_length=100)),
                ('dire', models.CharField(max_length=200)),
                ('mail', models.EmailField(max_length=200)),
                ('gene', models.CharField(choices=[('H', 'Hombre'), ('M', 'Mujer')], max_length=20)),
                ('fecha_naci', models.DateField(blank=True, null=True)),
                ('rol', models.CharField(choices=[('admin', 'Admin'), ('instructor', 'Instructor'), ('aprendiz', 'Aprendiz'), ('lider', 'Lider')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='T_lider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(max_length=200)),
                ('esta', models.CharField(max_length=200)),
                ('perfil', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='commons.t_perfil')),
            ],
        ),
        migrations.AddField(
            model_name='t_instructor',
            name='perfil',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='commons.t_perfil'),
        ),
        migrations.AddField(
            model_name='t_aprendiz',
            name='perfil',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='commons.t_perfil'),
        ),
        migrations.CreateModel(
            name='T_admin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(max_length=200)),
                ('esta', models.CharField(max_length=200)),
                ('perfil', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='commons.t_perfil')),
            ],
        ),
        migrations.AddField(
            model_name='t_guias',
            name='progra',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_programas'),
        ),
        migrations.CreateModel(
            name='T_competencias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('fase', models.CharField(choices=[('fase analisis', 'Fase Analisis'), ('fase planeacion', 'Fase Planeacion'), ('fase ejecucion', 'Fase Ejecucion'), ('fase evaluacion', 'Fase Evaluacion')], max_length=200)),
                ('progra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_programas')),
            ],
        ),
        migrations.AddField(
            model_name='t_actividades',
            name='progra',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_programas'),
        ),
        migrations.CreateModel(
            name='T_raps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('compe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_competencias')),
            ],
        ),
        migrations.CreateModel(
            name='T_actividades_recurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acti_docu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_actividades_documento')),
                ('recu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_recursos')),
            ],
        ),
        migrations.AddField(
            model_name='t_aprendiz',
            name='repre_legal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_representante_legal'),
        ),
    ]
