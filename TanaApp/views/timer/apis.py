from rest_framework import generics, permissions
from TanaApp.models import DbTimer
from .serializers import TimerSerializer

class TimerListCreateView(generics.ListCreateAPIView):
    queryset = DbTimer.objects.all()
    serializer_class = TimerSerializer
    permission_classes = [permissions.IsAuthenticated]

class TimerRetrieveView(generics.RetrieveAPIView):
    queryset = DbTimer.objects.all()
    serializer_class = TimerSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class BuildingTimersView(generics.ListAPIView):
    serializer_class = TimerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs['building_id']
        return DbTimer.objects.filter(building_id=building_id)