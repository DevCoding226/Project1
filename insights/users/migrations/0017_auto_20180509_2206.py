# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-05-09 22:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20180119_1753'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('email',)]),
        ),
    ]
