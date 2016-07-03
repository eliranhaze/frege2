# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-03 14:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0014_auto_20160703_1414'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useranswer',
            name='user_chapter',
        ),
        migrations.AddField(
            model_name='useranswer',
            name='submission',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='logic.ChapterSubmission', verbose_name='\u05d4\u05d2\u05e9\u05ea \u05e4\u05e8\u05e7'),
            preserve_default=False,
        ),
    ]