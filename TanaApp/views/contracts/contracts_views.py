from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import now
from TanaApp.models import DbElevator, DbContract, ContratE, DbWarranty, DbBuilding, DBPartialPyment
from .serializers import ContractManageSerializer
from django.db.models import Q
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from TanaApp.views.partial_payments.serializers import PartialPaymentManageSerializer
from TanaApp.views.extras.serializers import ExtraManageSerializer
from TanaApp.views.discounts.serializers import DiscountManageSerializer
from TanaApp.contract_payment import compute_contract_totals, get_payment_status_constraints, sync_contract_payment_status

@login_required
def contract_dashboard(request, building_id):
    building = get_object_or_404(DbBuilding, id=building_id)

    # Elevators in the building
    all_elevators = DbElevator.objects.filter(building_id=building_id)

    # Elevators under active contract
    '''
    contracted_elevator_ids = DBContractElevator.objects.filter(
        contract__payed=ContratE.TWO,
        contract__end_date__gte=now()
    ).values_list('elevator_id', flat=True)
    '''
    contracted_elevator_ids = DbContract.objects.filter(
        payed=ContratE.TWO,
        end_date__gte=now()
    ).values_list('elevators__id', flat=True)

    # Elevators still under active warranty
    under_warranty_ids = DbWarranty.objects.filter(
        end_date__gte=now()
    ).values_list('elevator_id', flat=True)

    # Valid elevators: not under contract and not under warranty
    valid_elevators = all_elevators.exclude(
        Q(id__in=contracted_elevator_ids) | Q(id__in=under_warranty_ids)
    )

    # Existing contracts under this building
    building_contracts = DbContract.objects.filter(
        building_id=building_id,
        payed=3
    )

    # Expired contracts
    expired_contracts = DbContract.objects.filter(
        end_date__lt=now()
    ).exclude(payed=3)

    return render(request, 'pages/webs/contracts/dashboard.html', {
        'building': building,
        'elevators': valid_elevators,
        'building_contracts': building_contracts,
        'expired_contracts': expired_contracts,
    })


class ContractCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/webs/contracts/calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_id = self.kwargs.get('id')
        context['contract'] = get_object_or_404(DbContract, id=contract_id)
        return context

class ContractManageView(TemplateView):
    template_name = "pages/webs/contracts/contract_manage.html"

    def get_context_data(self, **kwargs):
        ctx      = super().get_context_data(**kwargs)
        contract = get_object_or_404(
            DbContract.objects.select_related('building').prefetch_related(
                'elevators', 'extra', 'discount', 'partial'
            ),
            id=kwargs['id'],
        )
        ctx['contract'] = contract
        ctx['contract_data'] = ContractManageSerializer(contract).data
        from TanaApp.views.contracts.serializers import ContractUpdateSerializer
        ctx['contract_form'] = ContractUpdateSerializer(instance=contract)
        ctx['partial_form'] = PartialPaymentManageSerializer(
            instance=contract.partial.first()
        )
        ctx['extras_form'] = ExtraManageSerializer(instance=contract.extra.first())
        ctx['discounts_form'] = DiscountManageSerializer(instance=contract.discount.first())

        ctx['contract_id'] = contract.id
        sync_contract_payment_status(contract, save=True)
        contract.refresh_from_db(fields=['payed'])
        payment_constraints = get_payment_status_constraints(contract)
        ctx['payment_summary'] = payment_constraints
        ctx['can_mark_fully_paid'] = payment_constraints['can_mark_fully_paid']
        ctx['can_mark_not_paid'] = payment_constraints['can_mark_not_paid']
        ctx['can_mark_partial_paid'] = payment_constraints['can_mark_partial_paid']

        now = timezone.now()
        if contract.end_date and contract.start_date:
            end = contract.end_date
            start = contract.start_date
            ctx['contract_is_active'] = end >= now
            ctx['days_remaining'] = max(0, (end.date() - now.date()).days) if end >= now else 0
            total_days = max(1, (end.date() - start.date()).days)
            elapsed = max(0, (now.date() - start.date()).days)
            ctx['contract_progress_pct'] = min(100, round(100 * elapsed / total_days))
        else:
            ctx['contract_is_active'] = False
            ctx['days_remaining'] = 0
            ctx['contract_progress_pct'] = 0

        return ctx