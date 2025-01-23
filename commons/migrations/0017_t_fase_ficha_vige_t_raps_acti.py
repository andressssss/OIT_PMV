# Generated by Django 5.1.4 on 2024-12-21 01:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0016_alter_t_raps_fase'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_fase_ficha',
            name='vige',
            field=models.CharField(default='No', max_length=100),
        ),
        migrations.CreateModel(
            name='T_raps_acti',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_acti')),
                ('rap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_raps')),
            ],
            options={
                'db_table': 'T_raps_acti',
                'managed': True,
            },
        ),
    ]