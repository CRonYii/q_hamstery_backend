from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..serializers import ShowSubscriptionSerializer
from ..models.show_subscription import ShowSubscription

# Create your views here.

class ShowSubscriptionView(viewsets.ModelViewSet):
    queryset = ShowSubscription.objects.all()
    serializer_class = ShowSubscriptionSerializer
    filterset_fields = {
        'season': ['exact'],
    }
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['priority']
    ordering = ['priority']

    @action(methods=['post'], detail=True)
    def monitor(self, request, pk=None):
        sub: ShowSubscription = self.get_object()
        sub.monitor_step()
        return Response('Ok')
