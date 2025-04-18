# Generated by Django 5.1.4 on 2025-01-10 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0046_alter_t_docu_archi'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_insti_edu',
            name='coordi',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='coordi_mail',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='coordi_tele',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='esta',
            field=models.CharField(choices=[('articulado', 'Articulado'), ('articulado nuevo', 'Articulado nuevo')], default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='insti_mail',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='recto',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='recto_tel',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='t_insti_edu',
            name='vigen',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
