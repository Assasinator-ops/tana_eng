from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction
from TanaApp.models import DBPartialPyment, DbContract
from TanaApp.contract_payment import resync_contract_payment_status
from .serializers import PartialPaymentSerializer


class PartialPaymentCreateView(generics.CreateAPIView):
    queryset = DBPartialPyment.objects.all()
    serializer_class = PartialPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        resync_contract_payment_status(instance.contract_id)


class PartialPaymentRetrieveView(generics.RetrieveAPIView):
    serializer_class = PartialPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        contract_id = self.kwargs['contract_id']
        try:
            return DBPartialPyment.objects.get(contract_id=contract_id)
        except DBPartialPyment.DoesNotExist:
            raise NotFound("Partial payment not found")


class PartialPaymentUpdateView(generics.UpdateAPIView):
    serializer_class = PartialPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        contract_id = kwargs['contract_id']
        amount = request.data.get('amount')
        total = request.data.get('total')

        if amount is None:
            raise ValidationError({'amount': 'This field is required.'})

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError({'amount': 'Enter a valid payment amount.'})
        if amount <= 0:
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})

        try:
            contract = DbContract.objects.get(id=contract_id)
        except DbContract.DoesNotExist:
            raise NotFound("Contract not found")

        try:
            partial_payment = DBPartialPyment.objects.get(contract_id=contract_id)
            new_amount = partial_payment.amount + amount
        except DBPartialPyment.DoesNotExist:
            initial_total = float(total) if total is not None else 0.0
            partial_payment = DBPartialPyment.objects.create(
                contract=contract,
                amount=amount,
                total=initial_total,
            )
            resync_contract_payment_status(contract_id)
            return Response(self.get_serializer(partial_payment).data)

        if new_amount > partial_payment.total:
            remaining = partial_payment.total - partial_payment.amount
            raise ValidationError(
                f"Payment cannot exceed total. Remaining: {remaining}"
            )

        partial_payment.amount = new_amount
        if total is not None:
            partial_payment.total = float(total)
        partial_payment.save()

        resync_contract_payment_status(contract_id)
        contract.refresh_from_db()

        return Response(self.get_serializer(partial_payment).data)


class PartialDeleteView(generics.DestroyAPIView):
    queryset = DBPartialPyment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'contract_id'

    def perform_destroy(self, instance):
        contract_id = instance.contract_id
        super().perform_destroy(instance)
        resync_contract_payment_status(contract_id)
