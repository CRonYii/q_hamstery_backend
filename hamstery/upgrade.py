import logging

from django.apps import AppConfig
from django.db.models.signals import pre_migrate, post_migrate
from django.db.migrations.recorder import MigrationRecorder

logger = logging.getLogger(__name__)

def upgrade_tvshow_lib_id():
    from hamstery.models import TvShow
    for show in TvShow.objects.all():
        show.lib = show.storage.lib
        show.save()

upgrade_handler = {
    '0016_tvshow_lib': upgrade_tvshow_lib_id
}

pre_migration = None

def upgrade_pre_migration_handler(sender: AppConfig, **kwargs):
    global pre_migration
    pre_migration = MigrationRecorder.Migration.objects.filter(app=sender.name).latest('id')

def upgrade_post_migration_handler(sender: AppConfig, **kwargs):
    migrations = MigrationRecorder.Migration.objects.filter(app=sender.name, id__gt=pre_migration.id)
    for migration in migrations:
        if migration.name not in upgrade_handler:
            continue
        logger.info('Running migration uprade handler for "%s"' % (migration.name))
        upgrade_handler[migration.name]()

def register_upgrade_hook(app: AppConfig):
    pre_migrate.connect(upgrade_pre_migration_handler, sender=app)
    post_migrate.connect(upgrade_post_migration_handler, sender=app)
