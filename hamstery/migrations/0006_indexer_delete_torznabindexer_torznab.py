# Generated by Django 4.1 on 2022-12-20 18:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hamstery', '0005_tvshow_air_date_alter_tvepisode_air_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Indexer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
            ],
        ),
        migrations.DeleteModel(
            name='TorznabIndexer',
        ),
        migrations.CreateModel(
            name='Torznab',
            fields=[
                ('indexer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='hamstery.indexer')),
                ('url', models.CharField(max_length=1024)),
                ('apikey', models.CharField(max_length=128)),
            ],
            bases=('hamstery.indexer',),
        ),
    ]
