# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-24 11:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0008_organization_report_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='report_order',
            field=models.PositiveIntegerField(blank=True, default=1, verbose_name='Ordering in reports'),
        ),
    ]
