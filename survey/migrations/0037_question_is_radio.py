# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-04-20 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0036_auto_20180221_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_radio',
            field=models.BooleanField(default=False, verbose_name='Allow to select only one'),
        ),
    ]
