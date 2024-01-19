from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from hamstery.models.singleton import SingletonModel


class HamsterySettings(SingletonModel):
    qbittorrent_host = models.CharField(
        max_length=2048, blank=True, default='')
    qbittorrent_port = models.CharField(
        max_length=5, blank=True, default='')
    qbittorrent_username = models.CharField(
        max_length=255, blank=True, default='')
    qbittorrent_password = models.CharField(
        max_length=255, blank=True, default='')

    plex_enable = models.BooleanField(default=False)
    plex_url = models.CharField(
        max_length=2048, blank=True, default='')
    plex_token = models.CharField(
        max_length=2048, blank=True, default='')

    openai_api_key = models.CharField(
        max_length=2048, blank=True, default='')
    class TitleParserMode(models.IntegerChoices):
        DISABLED = 1
        PRIMARY = 2
        STANDBY = 3
    openai_title_parser_mode = models.IntegerField(choices=TitleParserMode.choices, default=TitleParserMode.DISABLED)
    openai_title_parser_model = models.CharField(
        max_length=255, blank=True, default='')

    def __str__(self) -> str:
        return 'Hamstery Settings'
