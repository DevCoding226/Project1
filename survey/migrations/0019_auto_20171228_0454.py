# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-12-28 04:54
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0018_auto_20171225_1341'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='end',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 28, 4, 53, 47, 283636, tzinfo=utc), verbose_name='Ends at'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='survey',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 28, 4, 54, 0, 362472, tzinfo=utc), verbose_name='Starts at'),
            preserve_default=False,
        ),
    ]
