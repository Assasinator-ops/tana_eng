from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from TanaApp.models import DbElevator, DbWarranty
from .serializers import ElevatorSerializer


class ElevatorListCreateView(generics.ListCreateAPIView):
    queryset = DbElevator.objects.all()
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        elevator = serializer.save()

        # Create warranty
        warranty_months = int(self.request.data.get('warranty_months', 12))
        DbWarranty.objects.create(
            elevator=elevator,
            start_date=timezone.now(),
            end_date=timezone.now() + relativedelta(months=+warranty_months)
        )
        return redirect('elevator-dashboard')


class ElevatorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DbElevator.objects.all()
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        instance = serializer.save()

        # Update warranty
        warranty_months = int(self.request.data.get('warranty_months', 0))
        DbWarranty.objects.filter(elevator=instance).update(
            end_date=instance.warranty.start_date + relativedelta(months=+warranty_months)
        )


class ElevatorWarrantyListView(generics.ListAPIView):
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs['building_id']
        return DbElevator.objects.filter(
            building_id=building_id
        ).prefetch_related('warranty')


class ElevatorCheckView(generics.ListAPIView):
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs['building_id']
        return DbElevator.objects.filter(
            building_id=building_id,
            elevatorC__isnull=True  # No contract relation
        )


class ElevatorSearchView(generics.ListAPIView):
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        search_id = self.request.query_params.get('id', '')
        return DbElevator.objects.filter(id__icontains=search_id)