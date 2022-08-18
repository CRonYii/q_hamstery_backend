from django.urls import include, path

from rest_framework import routers
from hamstery import views

router = routers.DefaultRouter()
router.register(r'torznab', views.TorznabIndexerView, 'torznab')

urlpatterns = [
    path('api/', include(router.urls)),
]