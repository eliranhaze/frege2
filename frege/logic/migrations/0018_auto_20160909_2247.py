# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-09 19:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0017_auto_20160909_2223'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='useranswer',
            unique_together=set([('chapter', 'user', '_cq', '_oq', '_fq', '_tq', '_mq', '_dq', 'is_followup')]),
        ),
    ]