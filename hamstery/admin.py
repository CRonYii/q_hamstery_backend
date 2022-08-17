from django.contrib import admin
from .models import  TorznabIndexer

# Register your models here.

@admin.register(TorznabIndexer)
class TorznabIndexerAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'apikey']
