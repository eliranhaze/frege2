# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-29 18:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0022_auto_20160913_0230'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapter',
            name='url',
            field=models.URLField(default='http://www.google.com', verbose_name='\u05e8\u05e9\u05d9\u05de\u05ea \u05e9\u05d0\u05dc\u05d5\u05ea'),
            preserve_default=False,
        ),
    ]
