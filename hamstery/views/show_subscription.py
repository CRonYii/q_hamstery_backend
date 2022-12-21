from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers import ShowSubscriptionSerializer
from ..models.show_subscrition import ShowSubscription

# Create your views here.

class ShowSubscriptionView(viewsets.ModelViewSet):
    queryset = ShowSubscription.objects.all()
    serializer_class = ShowSubscriptionSerializer

    @action(methods=['post'], detail=True)
    def monitor(self, request, pk=None):
        sub: ShowSubscription = self.get_object()
        sub.monitor_step()
        return Response('Ok')
