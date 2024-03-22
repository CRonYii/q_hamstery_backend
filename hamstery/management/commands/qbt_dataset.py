import json
import logging
from pathlib import Path

from ..command import HamsteryCommand

from hamstery.qbittorrent import qbt
from hamstery.utils import is_video_extension

logger = logging.getLogger(__name__)

class FileTree:
    '''
    interface IFile {
        type: 'file',
        index: number,
    }
    interface IDir extends Record<string, IFile | 'dir'> {
        type: 'dir',
    }

    function matchFileToEpisode(root: IDir) {}
    '''

    def __init__(self):
        self.data = {
            'type': 'dir',
            'entries': {},
        }

    def add_file(self, filename: str, meta: dict):
        path = Path(filename)
        parents = list(map(lambda p: p.name, path.parents))
        parents.reverse()
        basename = path.name
        data = self.locate_dir(self.data, parents)
        data['entries'][basename] = {
            'type': 'file',
            **meta,
        }
    
    def locate_dir(self, data, keys):
        key = keys[0]
        if key == '':
            dir_data = data
        else:
            if key not in data['entries']:
                data['entries'][key] = {
                    'type': 'dir',
                    'entries': {},
                }
            dir_data = data['entries'][key]
        if len(keys) == 1:
            return dir_data
        return self.locate_dir(dir_data, keys[1:])

class FileCount:
    
    def __init__(self):
        self.data = {}
        
    def add_file(self, filename: str):
        filepath = str(Path(filename).parent)
        if filepath not in self.data:
            self.data[filepath] = 0
        self.data[filepath] += 1


class Command(HamsteryCommand):
    help = 'Helpful tool to create dataset out of QBittorrent connection'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "dataset",
            choices=['filetree', 'filecount'],
            help=(
                "The type of dataset that needs to be generated."
            )
        )
        # 30d2d2caee42411c1c70c89a2a866374c2a3aad9
        parser.add_argument(
            "--hash",
            required=True,
            help=(
                "Hash of the target torrent."
            ),
        )

    def hamstery_handle(self, *args, **options):
        dataset = options['dataset']
        torrent_hash = options['hash']
        self.test_qbt()

        if dataset == 'filetree':
            self.get_torrent_filetree(torrent_hash)
        elif dataset == 'filecount':
            self.get_torrent_filecount(torrent_hash)
        
    def test_qbt(self):
        [running, _] = qbt.test_connection()
        if not running:
            exit()

    def get_torrent_filetree(self, torrent_hash):
        files = qbt.client.torrents_files(torrent_hash=torrent_hash)
        tree = FileTree()
        for file in files:
            if not is_video_extension(file['name']):
                continue
            tree.add_file(file['name'], { 'index': file['index'] })

        # Write to file
        fp = self.prepare_output_file(torrent_hash + '_filetree.json', mode='+w', encoding='utf-8')
        json.dump(tree.data, fp, indent=2, ensure_ascii=False)

    def get_torrent_filecount(self, torrent_hash):
        files = qbt.client.torrents_files(torrent_hash=torrent_hash)
        count = FileCount()
        for file in files:
            if not is_video_extension(file['name']):
                continue
            count.add_file(file['name'])

        # Write to file
        fp = self.prepare_output_file(torrent_hash + '_filecount.json', mode='+w', encoding='utf-8')
        json.dump(count.data, fp, indent=2, ensure_ascii=False)
