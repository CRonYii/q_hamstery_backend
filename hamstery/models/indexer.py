from django.db import models
import requests
import logging
from lxml import etree

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
    
    def __str__(self):
        return self.name


class Torznab(Indexer):
    url = models.CharField(max_length=1024)
    apikey = models.CharField(max_length=128)
    cat = models.CharField(max_length=128, blank=True, default='')

    def search(self, query='') -> Result:
        try:
            r = requests.get(self.url, params={
                             'apikey': self.apikey, 'q': query, 't': 'search', 'cat': self.cat, })
            if not r.ok:
                return failure('Torznab %s(%s): HTTP Error %d %s' % (self.name, self.url, r.status_code, r.reason))
            tree = etree.fromstring(r.content)
            if tree.tag == "error":
                return failure(tree.find('description'))
            channel = tree.find('channel')
            torrents = []
            for item in channel.iter('item'):
                try:
                    torrent = {
                        'title': item.find('title').text,
                        'link': item.find('link').text,
                        'size': item.find('size').text,
                        'pub_date': item.find('pubDate').text
                    }
                    magneturl = item.xpath('torznab:attr[@name=\'magneturl\']', namespaces=tree.nsmap)
                    if len(magneturl) != 0:
                        torrent['magneturl'] = magneturl[0].get('value')
                    torrents.append(torrent)
                except:
                    continue

            return success(torrents)
        except requests.exceptions.RequestException as e:
            logger.warning(str(e))
            return failure(str(e))

    def caps(self):
        try:
            r = requests.get(self.url, params={
                             'apikey': self.apikey, 't': 'caps', })
            if not r.ok:
                return failure('Torznab %s(%s): HTTP Error %d %s' % (self.name, self.url, r.status_code, r.reason))
            tree = etree.fromstring(r.content)
            if tree.tag == "error":
                return failure(tree.get('description'))
            caps = {
                'searching': {},
                'categories': [],
            }
            searching = tree.find('searching')
            for item in searching.getchildren():
                caps['searching'][item.tag] = item.attrib
            categories = tree.find('categories')
            for item in categories.getchildren():
                cat = dict(item.attrib)
                cat['subcat'] = []
                for subcat in item.getchildren():
                    cat['subcat'].append(subcat.attrib)
                caps['categories'].append(cat)

            return success(caps)
        except requests.exceptions.RequestException as e:
            logger.warning(str(e))
            return failure(str(e))