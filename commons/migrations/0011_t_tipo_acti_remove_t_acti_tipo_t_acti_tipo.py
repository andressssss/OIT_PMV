# Generated by Django 5.1.4 on 2024-12-20 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0010_remove_t_acti_progra_t_ficha_num_matri_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='T_tipo_acti',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'db_table': 'T_tipo_acti',
                'managed': True,
            },
        ),
        migrations.RemoveField(
            model_name='t_acti',
            name='tipo',
        ),
        migrations.AddField(
            model_name='t_acti',
            name='tipo',
            field=models.ManyToManyField(to='commons.t_tipo_acti'),
        ),
    ]
