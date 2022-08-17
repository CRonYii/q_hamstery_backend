from django.db import models

# Create your models here.

class TorznabIndexer(models.Model):
    name = models.CharField(max_length=120)
    url = models.CharField(max_length=1024)
    apikey = models.CharField(max_length=128)
