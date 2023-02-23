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

    def __str__(self) -> str:
        return 'Hamstery Settings'
