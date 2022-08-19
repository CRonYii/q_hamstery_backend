from django.db import models
import requests
from xml.etree import ElementTree

from ..utils import Result, failure, success

# Create your models here.

class TorznabIndexer(models.Model):
    name = models.CharField(max_length=120)
    url = models.CharField(max_length=1024)
    apikey = models.CharField(max_length=128)

    def search(self, query='') -> Result:
        print('search "%s" via "%s"' % (query, self.name))
        try:
            r = requests.get(self.url, params={'apikey': self.apikey, 'q': query, 't': 'tvsearch', 'cat': '',})
            if not r.ok:
                return failure('Indexer %s(%s): HTTP %d %s' % (self.name, self.url, r.status_code, r.reason))
            tree = ElementTree.fromstring(r.content)
            if tree.tag == "error":
                return failure(tree.get('description'))
            channel = tree[0]
            torrents = []
            for item in channel.iter('item'):
                try:
                    torrent = {
                        'title' : item.find('title').text,
                        'link' : item.find('link').text,
                        'size' : item.find('size').text,
                        'pub_date' : item.find('pubDate').text
                    }
                    torrents.append(torrent)
                except:
                    continue
            
            return success(torrents)
        except requests.exceptions.RequestException as e:
            return failure(str(e))