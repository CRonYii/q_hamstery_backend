import json
import logging

from hamstery.tmdb import tmdb_tv_show_details_sync

from ..command import HamsteryCommand

logger = logging.getLogger(__name__)

class Command(HamsteryCommand):
    help = 'Helpful tool to create dataset out of TMDB API'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "dataset",
            choices=['show'],
            help=(
                "The type of dataset that needs to be generated."
            )
        )
        # 30d2d2caee42411c1c70c89a2a866374c2a3aad9
        parser.add_argument(
            "--id",
            required=True,
            help=(
                "id of the TMDB object."
            ),
        )
        parser.add_argument(
            "--lang",
            default='en',
            help=(
                "Language the result will be."
            ),
        )

    def hamstery_handle(self, *args, **options):
        dataset = options['dataset']
        tmdb_id = options['id']
        lang = options['lang']

        if dataset == 'show':
            self.get_show(tmdb_id, lang)

    def get_show(self, tmdb_id, lang):
        res = tmdb_tv_show_details_sync(int(tmdb_id), lang)
        if not res.success:
            return
        tmdb_data = res.data()
        data = {
            'name': tmdb_data['name'],
            'original_name': tmdb_data['original_name'],
            'number_of_seasons': tmdb_data['number_of_seasons'],
            'seasons': []
        }
        for season in tmdb_data['seasons']:
            season_data = {
                'name': season['name'],
                'season_number': season['season_number'],
                'episode_count': season['episode_count'],
            }
            data['seasons'].append(season_data)

        # Write to file
        fp = self.prepare_output_file(data['name'] + '.json', mode='+w', encoding='utf-8')
        json.dump(data, fp, indent=2, ensure_ascii=False)
