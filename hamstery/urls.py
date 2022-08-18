from django.urls import include, path

from rest_framework import routers
from hamstery import views

router = routers.DefaultRouter()
router.register(r'torznab', views.TorznabIndexerView, 'torznab-indexer')
router.register(r'tvlib', views.TvLibraryView, 'tv-library')
router.register(r'tvstorage', views.TvStorageView, 'tv-storage')

urlpatterns = [
    path('api/', include(router.urls)),
]