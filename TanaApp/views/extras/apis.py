from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from TanaApp.models import DbExtra
from TanaApp.contract_payment import resync_contract_payment_status
from .serializers import ExtraSerializer, ExtraManageSerializer

class ContractExtrasView(generics.ListCreateAPIView):
    serializer_class = ExtraManageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        return DbExtra.objects.filter(contract_id=contract_id)

    def perform_create(self, serializer):
        contract_id = self.kwargs['contract_id']
        serializer.save(contract_id=contract_id)
        resync_contract_payment_status(contract_id)

class ExtraRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = DbExtra.objects.all()
    serializer_class = ExtraSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def handle_exception(self, exc):
        if isinstance(exc, DbExtra.DoesNotExist):
            return Response(
                {'detail': 'Not found bro'},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

class ExtraDeleteView(generics.DestroyAPIView):
    queryset = DbExtra.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_destroy(self, instance):
        contract_id = instance.contract_id
        super().perform_destroy(instance)
        resync_contract_payment_status(contract_id)