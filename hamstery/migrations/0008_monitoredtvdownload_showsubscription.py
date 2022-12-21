# Generated by Django 4.1 on 2022-12-21 05:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hamstery', '0007_torznab_cat'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, parent_link=True, related_name='subs', to='hamstery.tvseason')),
                ('indexer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, parent_link=True, related_name='subs', to='hamstery.indexer')),
                ('query', models.CharField(max_length=1024)),
                ('priority', models.PositiveIntegerField()),
                ('offset', models.PositiveIntegerField(blank=True, null=True)),
                ('exclude', models.CharField(blank=True, default='', max_length=512)),
                ('done', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='MonitoredTvDownload',
            fields=[
                ('tvdownload_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='hamstery.tvdownload')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, parent_link=True, related_name='downloads', to='hamstery.showsubscription')),
            ],
            options={
                'abstract': False,
            },
            bases=('hamstery.tvdownload',),
        ),
    ]