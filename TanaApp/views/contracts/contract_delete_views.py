from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from TanaApp.models import DbContract
from TanaApp.contract_payment import compute_contract_totals
from TanaApp.models import DbContractScar


class ContractSoftDeleteView(LoginRequiredMixin, View):
    """Soft-delete contract.

    Hybrid rule:
    - Always soft-delete (hide from UI)
    - If customer already paid (amount_paid > 0.01), create a scar reminder
    """

    def post(self, request, id):
        contract = get_object_or_404(DbContract, id=id, deleted_at__isnull=True)

        totals = compute_contract_totals(contract)
        amount_paid = totals.get('amount_paid', 0.0)

        # Always soft-delete
        contract.deleted_at = timezone.now()
        contract.save(update_fields=['deleted_at'])

        # If customer has paid, create scar
        if amount_paid > 0.01:
            DbContractScar.objects.create(
                contract=contract,
                deleted_at=timezone.now(),
                deleted_by=request.user,
                note='Contract deleted while customer has paid.',
            )

        messages.success(request, f"Contract #{contract.id} deleted successfully.")
        # redirect back to elevator detail (fallback)
        return redirect(request.GET.get('next') or request.META.get('HTTP_REFERER') or 'dashboard')


class ContractScarDeleteView(LoginRequiredMixin, View):
    """Admin-only hard delete of scar."""

    def post(self, request, scar_id):
        if not request.user.is_superuser:
            messages.error(request, 'Only admin can delete scars.')
            return redirect(request.GET.get('next') or 'dashboard')

        scar = get_object_or_404(DbContractScar, id=scar_id)
        scar.delete()
        messages.success(request, 'Scar deleted.')
        return redirect(request.GET.get('next') or 'dashboard')

