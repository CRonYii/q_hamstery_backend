# Generated by Django 4.1 on 2022-12-22 02:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamstery', '0008_monitoredtvdownload_showsubscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showsubscription',
            name='offset',
            field=models.PositiveIntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='showsubscription',
            name='priority',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
