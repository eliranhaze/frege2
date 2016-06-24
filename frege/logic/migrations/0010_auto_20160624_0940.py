# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-24 09:40
from __future__ import unicode_literals

from django.db import migrations, models
import logic.models


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0009_auto_20160624_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deductionquestion',
            name='text',
            field=models.CharField(max_length=60, validators=[logic.models.validate_argument], verbose_name='\u05d8\u05d9\u05e2\u05d5\u05df'),
        ),
        migrations.AlterField(
            model_name='truthtablequestion',
            name='text',
            field=models.CharField(max_length=60, validators=[logic.models.validate_truth_table], verbose_name='\u05d8\u05e7\u05e1\u05d8'),
        ),
    ]
