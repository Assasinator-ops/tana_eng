from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404

from TanaApp.models import DbElevator, DbElevatorExtra, DbElevatorDiscount
from .extras_discount_serializers import (
    ElevatorExtraManageSerializer,
    ElevatorDiscountManageSerializer,
)


class ElevatorExtraListCreateView(generics.ListCreateAPIView):

    serializer_class = ElevatorExtraManageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        elevator_id = self.kwargs["elevator_id"]
        return DbElevatorExtra.objects.filter(elevator_id=elevator_id).order_by("id")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["elevator_id"] = self.kwargs["elevator_id"]
        return ctx


class ElevatorExtraRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ElevatorExtraManageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        elevator_id = self.kwargs["elevator_id"]
        return DbElevatorExtra.objects.filter(elevator_id=elevator_id).order_by("id")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["elevator_id"] = self.kwargs["elevator_id"]
        return ctx


class ElevatorDiscountListCreateView(generics.ListCreateAPIView):
    serializer_class = ElevatorDiscountManageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        elevator_id = self.kwargs["elevator_id"]
        return DbElevatorDiscount.objects.filter(elevator_id=elevator_id).order_by("id")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["elevator_id"] = self.kwargs["elevator_id"]
        return ctx


class ElevatorDiscountRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ElevatorDiscountManageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        elevator_id = self.kwargs["elevator_id"]
        return DbElevatorDiscount.objects.filter(elevator_id=elevator_id).order_by("id")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["elevator_id"] = self.kwargs["elevator_id"]
        return ctx

