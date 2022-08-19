from django.urls import include, path

from rest_framework import routers
from hamstery import views

router = routers.DefaultRouter()
router.register(r'torznab', views.TorznabIndexerView, 'torznab-indexer')
router.register(r'tvlib', views.TvLibraryView, 'tv-library')
router.register(r'tvstorage', views.TvStorageView, 'tv-storage')
router.register(r'tvshow', views.TvShowView, 'tv-show')
router.register(r'tvseason', views.TvSeasonView, 'tv-season')
router.register(r'tvepisode', views.TvEpisodeView, 'tv-episode')

urlpatterns = [
    path('api/', include(router.urls)),
    path('auth/login', views.login_view),
    path('auth/logout', views.logout_view),
]
