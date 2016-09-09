# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-09 18:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logic', '0014_auto_20160904_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='useranswer',
            name='_cq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.ChoiceQuestion'),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='_dq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.DeductionQuestion'),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='_fq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.FormulationQuestion'),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='_mq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.ModelQuestion'),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='_oq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.OpenQuestion'),
        ),
        migrations.AddField(
            model_name='useranswer',
            name='_tq',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='logic.TruthTableQuestion'),
        ),
        migrations.AlterUniqueTogether(
            name='useranswer',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='useranswer',
            name='question_number',
        ),
    ]
