from django.db import models
import requests
import logging
from xml.etree import ElementTree

from ..utils import Result, failure, success

logger = logging.getLogger(__name__)

# Create your models here.


class Indexer(models.Model):
    name = models.CharField(max_length=120)

    def search(self, query='') -> Result:
        try:
            torznab: Torznab = self.torznab
            return torznab.search(query)
        except Torznab.DoesNotExist:
            pass
        return failure('Indexer does not support searching')


class Torznab(Indexer):
    url = models.CharField(max_length=1024)
    apikey = models.CharField(max_length=128)

    def search(self, query='') -> Result:
        try:
            r = requests.get(self.url, params={
                             'apikey': self.apikey, 'q': query, 't': 'search', 'cat': '', })
            if not r.ok:
                return failure('Torznab %s(%s): HTTP Error %d %s' % (self.name, self.url, r.status_code, r.reason))
            tree = ElementTree.fromstring(r.content)
            if tree.tag == "error":
                return failure(tree.get('description'))
            channel = tree[0]
            torrents = []
            for item in channel.iter('item'):
                try:
                    torrent = {
                        'title': item.find('title').text,
                        'link': item.find('link').text,
                        'size': item.find('size').text,
                        'pub_date': item.find('pubDate').text
                    }
                    torrents.append(torrent)
                except:
                    continue

            return success(torrents)
        except requests.exceptions.RequestException as e:
            logger.warning(str(e))
            return failure(str(e))
