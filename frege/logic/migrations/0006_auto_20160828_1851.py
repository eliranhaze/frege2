# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-28 15:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0005_auto_20160828_1809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openanswer',
            name='user_answer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='logic.UserAnswer'),
        ),
    ]
