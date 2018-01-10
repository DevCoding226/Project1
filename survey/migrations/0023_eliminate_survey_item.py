# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-05 04:21
from __future__ import unicode_literals

from django.db import migrations


def items_to_questions(apps, schema_editor):
    SurveyItem = apps.get_model('survey', 'SurveyItem')
    order = 1
    for item in SurveyItem.objects.all():
        q = item.question
        q.survey_id = item.survey_id
        q.ordering = order
        order += 1
        q.save()


def questions_to_items(apps, schema_editor):
    raise Exception("Not supported")


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0022_auto_20180105_0420'),
    ]

    operations = [
        migrations.RunPython(items_to_questions, questions_to_items),
    ]