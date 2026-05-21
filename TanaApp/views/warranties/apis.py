from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from TanaApp.models import DbWarranty
from .serializers import (
    WarrantySerializer,
    WarrantyExpirySerializer,
    ExpiredContractSerializer
)
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View

class WarrantyListCreateView(generics.ListCreateAPIView):
    queryset = DbWarranty.objects.all()
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticated]

class WarrantyExpiringView(generics.ListAPIView):
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thirty_days_later = timezone.now() + timedelta(days=30)
        return DbWarranty.objects.filter(end_date__gt=thirty_days_later)

class BuildingWarrantyView(generics.ListAPIView):
    serializer_class = WarrantyExpirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs['building_id']
        return DbWarranty.objects.filter(
            elevator__building_id=building_id
        ).select_related('elevator')

class ActiveWarrantyView(generics.ListAPIView):
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbWarranty.objects.filter(end_date__gt=timezone.now())

class ExpiredWarrantyView(generics.ListAPIView):
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbWarranty.objects.filter(end_date__lt=timezone.now())

class AlmostExpiredView(generics.ListAPIView):
    serializer_class = ExpiredContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DbWarranty.objects.filter(
            end_date__lte=timezone.now() + timedelta(days=30),
            elevator__elevatorC__isnull=True
        ).select_related('elevator__building')



class VoidWarrantyView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, warranty_id):
        warranty = get_object_or_404(DbWarranty, id=warranty_id)
        today = now()

        # Void warranty by setting end_date to now (expires it immediately)
        warranty.end_date = today
        warranty.save(update_fields=['end_date'])

        messages.success(request, f"Warranty #{warranty.id} has been voided and expired.")

        # Redirect back to elevator detail page
        return redirect('elevator-detail-page', id=warranty.elevator.id)
