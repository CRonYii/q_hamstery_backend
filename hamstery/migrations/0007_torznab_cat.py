# Generated by Django 4.1 on 2022-12-20 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamstery', '0006_indexer_delete_torznabindexer_torznab'),
    ]

    operations = [
        migrations.AddField(
            model_name='torznab',
            name='cat',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
