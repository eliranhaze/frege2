# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-31 16:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0006_auto_20160828_1851'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValuesQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(default=0, null=True, verbose_name='\u05de\u05e1\u05e4\u05e8')),
                ('table_type', models.CharField(choices=[('F', '\u05e0\u05d5\u05e1\u05d7\u05d4'), ('S', '\u05e7\u05d1\u05d5\u05e6\u05d4'), ('A', '\u05d8\u05d9\u05e2\u05d5\u05df')], max_length=1, null=True, verbose_name='\u05e1\u05d5\u05d2')),
                ('formula', models.CharField(max_length=60, null=True, verbose_name='\u05e0\u05d5\u05e1\u05d7\u05d4/\u05d8\u05d9\u05e2\u05d5\u05df/\u05e7\u05d1\u05d5\u05e6\u05d4')),
                ('chapter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='logic.Chapter', verbose_name='\u05e4\u05e8\u05e7')),
            ],
            options={
                'ordering': ['number'],
                'abstract': False,
                'verbose_name': '\u05e9\u05d0\u05dc\u05ea \u05de\u05ea\u05df \u05e2\u05e8\u05db\u05d9\u05dd',
                'verbose_name_plural': '\u05e9\u05d0\u05dc\u05d5\u05ea \u05de\u05ea\u05df \u05e2\u05e8\u05db\u05d9\u05dd',
            },
        ),
        migrations.AlterUniqueTogether(
            name='valuesquestion',
            unique_together=set([('chapter', 'formula')]),
        ),
    ]
