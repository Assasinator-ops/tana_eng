from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from django.db import transaction, models
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now, timedelta
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from datetime import timedelta

from TanaApp.models import (
    DbContract, ContratE, DbElevator, DbDiscount, DBPartialPyment, DbWarranty
)
from TanaApp.contract_payment import PaymentStatusError, set_payment_status
from .serializers import (
    ContractCreateSerializer,
    ContractSerializer,
    ContractUpdateSerializer,
    TotalSerializer,
    ExpiredContractSerializer,
    ContractCalculatorSerializer,
    ContractManageSerializer,
)

class ContractListCreateView(generics.ListCreateAPIView):
    queryset = DbContract.objects.filter(payed__in=[1, 2])
    serializer_class = ContractCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        building_id = request.query_params.get('building') or request.data.get('building')
        next_url = request.query_params.get('next') or request.data.get('next')

        serializer = self.get_serializer(data=request.data, context={'building': building_id})
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()

        redirect_to = getattr(contract, '_redirect_to', None)
        headers = self.get_success_headers(serializer.data)
        print(f"redirect link = {redirect_to}")

        if redirect_to:
            return Response(status=status.HTTP_302_FOUND, headers={'Location': redirect_to})
        if next_url:
            return Response(status=status.HTTP_302_FOUND, headers={'Location': next_url})
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContractCalculatorAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        contract = get_object_or_404(DbContract, id=id)

        # Ensure the calculator serializer can render the 1st card (elevators list)
        # and the 2nd card totals without duplicating VAT/extra/discount.
        serializer = ContractCalculatorSerializer(contract)

        # Add elevators list payload for the UI.
        # UI expects: [{id, name, model, Total}]
        elevators_payload = [
            {
                'id': e.id,
                'name': e.name,
                'model': e.model,
                'Total': e.Total,
            }
            for e in contract.elevators.all()
        ]

        data = serializer.data
        data['elevators'] = elevators_payload
        return Response(data, status=status.HTTP_200_OK)


class ContractRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DbContract.objects.select_related('building').prefetch_related('elevators')
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ContractUpdateSerializer
        return ContractSerializer

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class BuildingContractsView(generics.ListAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs['building_id']
        return DbContract.objects.filter(
            building_id=building_id,
            payed=2
        ).prefetch_related('elevators')
        # .prefetch_related('contractElevator')

class ContractTotalView(generics.RetrieveAPIView):
    serializer_class = TotalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        contract = DbContract.objects.get(pk=self.kwargs['id'])
        '''
        elevator_total = DbElevator.objects.filter(
            elevatorC__contract_id=contract.id
        ).aggregate(total=models.Sum('Total'))['total'] or 0
        '''
        elevator_total = contract.elevators.aggregate(total=models.Sum('Total'))['total'] or 0

        discount = DbDiscount.objects.filter(
            contract_id=contract.id
        ).aggregate(total=models.Sum('discount_money'))['total'] or 0
        '''
        'eid': list(DBContractElevator.objects.filter(
                contract_id=contract.id
            ).values_list('elevator_id', flat=True))
        '''
        return {
            'Total': elevator_total - discount,
            'eid': list(contract.elevators.values_list('id', flat=True))
        }


class ExpiredContractsView(generics.ListAPIView):
    serializer_class = ExpiredContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.utils import timezone
        from django.db.models import F, Q
        return DbContract.objects.filter(
            end_date__lt=timezone.now()
        ).exclude(
            payed=3
        ).annotate(
            elevatorname=F('building__elevator__name'),
            elevatortotal=F('building__elevator__Total'),
            buildingname=F('building__name')
        )

class ContractRegisterView(View):
    def get(self, request):
        cid = request.GET.get('contract_id')
        wid = request.GET.get('warranty_id')
        contract = get_object_or_404(DbContract, id=cid)
        warranty = get_object_or_404(DbWarranty, id=wid)

        if warranty.elevator.building_id != contract.building_id:
            messages.error(request, "Contract and warranty must be for the same building.")
            return redirect('elevator-detail', id=warranty.elevator_id)

        today = now().date()

        warranty.end_date = today
        warranty.save(update_fields=['end_date'])

        # fix: compare .date() to .date()
        if not contract.start_date or contract.start_date.date() < today:
            contract.start_date = today
            contract.save(update_fields=['start_date'])

        contract.elevators.add(warranty.elevator)

        messages.success(request, "Warranty truncated and contract started today.")
        return redirect('elevator-detail-page', id=warranty.elevator_id)

class ContractCreateAttachAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        eid = request.data.get('elevator_id')
        bid = request.data.get('building_id')
        cid = request.data.get('contract_id')
        nc = request.data.get('new_contract')

        # 1) pick or create the contract
        if cid:
            contract = DbContract.objects.filter(id=cid, building_id=bid).first()
            if not contract:
                raise ValidationError("Contract not found for this building.")
        elif nc:
            payed = int(nc.get('payed', ContratE.ONE))
            contract = DbContract.objects.create(
                building_id=bid,
                start_date=nc['start_date'],
                end_date=nc['end_date'],
                paytime=nc['paytime'],
                payed=ContratE.ONE,
            )
            try:
                set_payment_status(contract, payed)
            except PaymentStatusError as exc:
                raise ValidationError({'payed': str(exc)}) from exc
        else:
            raise ValidationError("Provide either contract_id or new_contract payload.")

        # 2) attach elevator idempotently
        '''
        DBContractElevator.objects.get_or_create(
            contract=contract,
            elevator_id=eid
        )
        '''
        contract.elevators.add(eid)

        return Response(
            {"detail": f"Elevator attached to contract #{contract.id}"},
            status=status.HTTP_200_OK
        )

class ContractPaymentStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contract_id = request.GET.get("contract_id")
        new_status = request.GET.get("status")
        next_url = request.GET.get("next", "/")

        # Validate new status
        try:
            new_status = int(new_status)
            if new_status not in [1, 2, 3]:
                raise ValueError()
        except (TypeError, ValueError):
            messages.error(request, "Invalid payment status.")
            return redirect(next_url)

        contract = get_object_or_404(
            DbContract.objects.prefetch_related(
                'elevators', 'extra', 'discount', 'partial'
            ),
            id=contract_id,
        )
        try:
            set_payment_status(contract, new_status)
        except PaymentStatusError as exc:
            messages.error(request, str(exc))
            return redirect(next_url)

        messages.success(request, f"Payment status updated to: {contract.get_payed_display()}")
        return redirect(next_url)

class ContractUpdateAPIView(APIView):
    def post(self, request, contract_id):
        contract = get_object_or_404(DbContract, id=contract_id)
        serializer = ContractManageSerializer(contract, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            return redirect('contract-manage', id=contract.id)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractAuditTotalsView(APIView):
    """Run the contract-total auditor synchronously and return its stats.

    Useful for ops dashboards and for testing. Hits every contract in
    the database, so it is not free — but it is safe to call any time.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from TanaApp.audit import ContractTotalAuditor
        stats = ContractTotalAuditor.get().run_once(
            reason_label='Manual audit (API endpoint)',
        )
        return Response(stats, status=status.HTTP_200_OK)

    def get(self, request):
        # Convenience: GET also runs the audit so the URL is easy to bookmark.
        return self.post(request)

