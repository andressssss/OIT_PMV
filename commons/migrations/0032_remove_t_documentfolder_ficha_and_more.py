# Generated by Django 5.1.4 on 2024-12-24 23:03

import django.db.models.deletion
import mptt.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0031_t_documentfolder'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='t_documentfolder',
            name='ficha',
        ),
        migrations.RemoveField(
            model_name='t_documentfolder',
            name='url',
        ),
        migrations.CreateModel(
            name='T_DocumentContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('documento', 'Documento'), ('link', 'Enlace'), ('carpeta', 'Carpeta')], default='carpeta', max_length=50)),
                ('url', models.URLField(blank=True, null=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='commons.t_ficha')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='commons.t_documentcontent')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='commons.t_documentfolder')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]