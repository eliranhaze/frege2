# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-04 13:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0013_auto_20160904_1330'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='valuesquestion',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='valuesquestion',
            name='chapter',
        ),
        migrations.DeleteModel(
            name='ValuesQuestion',
        ),
    ]
