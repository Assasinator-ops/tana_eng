from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from TanaApp.models import DbElevator, DbWarranty
from .serializers import ElevatorSerializer
from TanaApp.contract_payment import compute_elevator_invoice


class ElevatorListCreateView(generics.ListCreateAPIView):
    queryset = DbElevator.objects.all()
    serializer_class = ElevatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Serializer.create() handles Total calculation automatically
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
        # Serializer.update() handles Total recalculation and contract total updates automatically
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


class ElevatorInvoiceAPIView(APIView):
    """API endpoint to generate invoice breakdown for a single elevator.

    Contract-level extras/discounts are NOT used here.
    This endpoint uses elevator-scoped models:
      - DbElevatorExtra
      - DbElevatorDiscount

    This avoids splitting/allocating contract extras across many elevators.
    """

    # Called from the elevator detail page.
    # Use AllowAny so invoice modal works even when session auth isn't recognized for API calls.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, elevator_id):
        try:
            elevator = DbElevator.objects.get(id=elevator_id)
        except DbElevator.DoesNotExist:
            raise NotFound("Elevator not found")

        # Use elevator-scoped totals
        extras_total = sum([(x.money or 0) for x in getattr(elevator, 'elevator_extra', []).all()])
        discounts_total = sum([(x.discount_money or 0) for x in getattr(elevator, 'elevator_discount', []).all()])

        # Pass both extras and discounts to compute_elevator_invoice
        extras_amounts = [float(extras_total)] if extras_total else None
        discounts_amounts = [float(discounts_total)] if discounts_total else None
        invoice_data = compute_elevator_invoice(elevator, extras=extras_amounts, discounts=discounts_amounts)

        invoice_data['elevator'] = {
            'id': elevator.id,
            'name': elevator.name,
            'model': elevator.model,
            'commission_number': elevator.commissionnumber,
        }

        return Response(invoice_data)

