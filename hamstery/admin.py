from django.contrib import admin
from .models import Indexer, Torznab, TvLibrary, TvStorage, TvShow, TvSeason, TvEpisode, TvDownload

# Register your models here.

@admin.register(Indexer)
class IndexerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Torznab)
class TorznabAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'url', 'apikey']

class TvStorageInline(admin.TabularInline):
    model = TvStorage

@admin.register(TvLibrary)
class TvLibraryAdmin(admin.ModelAdmin):
    list_display = ['name', 'lang']
    inlines = (TvStorageInline, )

class TvShowInline(admin.TabularInline):
    model = TvShow

@admin.register(TvStorage)
class TvStorageAdmin(admin.ModelAdmin):
    list_display = ['lib', 'path']
    inlines = (TvShowInline, )

class TvSeasonInline(admin.TabularInline):
    model = TvSeason

@admin.register(TvShow)
class TvShowAdmin(admin.ModelAdmin):
    list_display = ['tmdb_id', 'name', 'path']
    inlines = (TvSeasonInline, )

class TvEpisodeInline(admin.TabularInline):
    model = TvEpisode

@admin.register(TvSeason)
class TvSeasonAdmin(admin.ModelAdmin):
    list_display = ['tmdb_id', 'name', 'path']
    inlines = (TvEpisodeInline, )

@admin.register(TvDownload)
class TvDownloadAdmin(admin.ModelAdmin):
    list_display = ['hash', 'episode', 'done']