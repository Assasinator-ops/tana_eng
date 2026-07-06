from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from TanaApp.models import DbDiscount
from TanaApp.contract_payment import resync_contract_payment_status
from .serializers import DiscountSerializer, DiscountManageSerializer


class ContractDiscountsView(generics.ListCreateAPIView):
    serializer_class = DiscountManageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        return DbDiscount.objects.filter(contract_id=contract_id)

    def perform_create(self, serializer):
        contract_id = self.kwargs['contract_id']
        serializer.save(contract_id=contract_id)
        resync_contract_payment_status(contract_id)


class DiscountRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = DbDiscount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        if not self.get_object():
            raise NotFound("Discount not found")
        serializer.save()

class DiscountDeleteView(generics.DestroyAPIView):
    queryset = DbDiscount.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_destroy(self, instance):
        contract_id = instance.contract_id
        super().perform_destroy(instance)
        resync_contract_payment_status(contract_id)