# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-18 10:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0004_auto_20160618_0855'),
    ]

    operations = [
        migrations.AddField(
            model_name='useranswer',
            name='user_chapter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='logic.UserChapter', verbose_name='\u05e4\u05ea\u05e8\u05d5\u05df \u05e4\u05e8\u05e7'),
        ),
    ]