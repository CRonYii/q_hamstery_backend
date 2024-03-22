from pathlib import Path

from django.core.management.base import BaseCommand


class HamsteryCommand(BaseCommand):
    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument(
            "--output",
            default='dev_output',
            help=(
                "Output directory."
            ),
        )

        return parser
    
    def handle(self, *args, **options):
        self.output_folder = Path(options['output'])
        self.hamstery_handle(*args, **options)
    
    def hamstery_handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of HamsteryCommand must provide a hamstery_handle() method"
        )

    def prepare_output_file(self, filename, *args, **kwargs):
        self.prepare_output_folder()
        return open(self.output_folder / filename, *args, **kwargs)

    def prepare_output_folder(self):
        self.output_folder.mkdir(exist_ok=True)