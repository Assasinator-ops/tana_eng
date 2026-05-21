from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db.models import Q
from django.utils import timezone
from TanaApp.models import DbBuilding, DbElevator, DbContract, DbWarranty
from .serializers import (
    BuildingSerializer,
    BuildingCustomerSerializer,
    ElevatorContractSerializer,
    WarrantySerializer
)


class BuildingListCreateView(generics.ListCreateAPIView):
    queryset = DbBuilding.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated]


class BuildingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DbBuilding.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


class BuildingCustomerView(generics.ListAPIView):
    serializer_class = BuildingCustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner_id = self.kwargs['id']
        return DbBuilding.objects.filter(owner_id=owner_id).select_related('owner')


class BuildingElevatorView(generics.ListAPIView):
    serializer_class = ElevatorContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbBuilding.objects.prefetch_related('elevator_id').exclude(elevator_id__isnull=True)


class BuildingContractView(generics.ListAPIView):
    serializer_class = ElevatorContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbBuilding.objects.filter(
            elevator_id__contractC__contract__payed__in=[1, 2]
        ).distinct()


class BuildingWarrantyView(generics.ListAPIView):
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbBuilding.objects.filter(
            elevator_id__warranty__end_date__gt=timezone.now()
        ).distinct()


class BuildingSearchView(generics.ListAPIView):
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        search_type = self.request.query_params.get('type', 'building')
        query = self.request.query_params.get('name', '')

        if search_type == 'building':
            return DbBuilding.objects.filter(
                Q(name__icontains=query) |
                Q(name__istartswith=query) |
                Q(name__iendswith=query)
            )
        elif search_type == 'eid':
            return DbElevator.objects.filter(
                Q(id__icontains=query)
            )
        else:
            return DbBuilding.objects.none()