import logging
from django.core.management import call_command

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Install a specific version of Django'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help=(
                "Nominates a database to show migrations for. Defaults to the "
                '"default" database.'
            ),
        )

    def handle(self, *args, **options):
        # Get the database we're operating from
        db = options["database"]
        connection = connections[db]

        self.run_migration(connection, 'hamstery')

    def run_migration(self, connection, app_name):
        # Load migrations from disk/DB
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        graph = loader.graph

        shown = set()
        for node in graph.leaf_nodes(app_name):
            for plan_node in graph.forwards_plan(node):
                if plan_node not in shown and plan_node[0] == app_name:
                    title = plan_node[1]
                    applied_migration = loader.applied_migrations.get(plan_node)
                    # Mark it as applied/unapplied
                    if not applied_migration:
                        call_command('migrate', app_name, title)
                    shown.add(plan_node)