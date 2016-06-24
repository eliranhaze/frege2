# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-24 10:43
from __future__ import unicode_literals

from django.db import migrations, models
import logic.models


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0012_auto_20160624_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deductionquestion',
            name='formula',
            field=models.CharField(max_length=60, validators=[logic.models.validate_deduction_argument], verbose_name='\u05d8\u05d9\u05e2\u05d5\u05df'),
        ),
        migrations.AlterUniqueTogether(
            name='deductionquestion',
            unique_together=set([('chapter', 'formula')]),
        ),
        migrations.AlterUniqueTogether(
            name='truthtablequestion',
            unique_together=set([('chapter', 'formula')]),
        ),
    ]