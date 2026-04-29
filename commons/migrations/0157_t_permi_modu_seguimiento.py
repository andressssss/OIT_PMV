from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0156_t_consulta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_permi',
            name='modu',
            field=models.CharField(
                choices=[
                    ('departamentos', 'Departamentos'),
                    ('municipios', 'Municipios'),
                    ('usuarios', 'Usuarios'),
                    ('instructores', 'Instructores'),
                    ('aprendices', 'Aprendices'),
                    ('admin', 'Administradores'),
                    ('lideres', 'Lideres'),
                    ('cuentas', 'Cuentas'),
                    ('gestores', 'Gestores'),
                    ('fichas', 'Fichas'),
                    ('portafolios', 'Portafolios'),
                    ('instituciones', 'Instituciones'),
                    ('centros', 'Centros de Formacion'),
                    ('programas', 'Programas'),
                    ('competencias', 'Competencias'),
                    ('raps', 'Raps'),
                    ('dashboard', 'Dashboard'),
                    ('consultas', 'Usuarios de Consulta'),
                    ('seguimiento', 'Seguimiento (instructores y mayoría de edad)'),
                ],
                max_length=100,
            ),
        ),
    ]
