# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-09 07:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0031_add_therapeutic_areas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='active',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Is active'),
        ),
    ]
