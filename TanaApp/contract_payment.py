"""
Contract payment status rules tied to calculator totals (expected vs paid).
"""
from __future__ import annotations

from decimal import Decimal

from TanaApp.models import ContratE, DbContract

TOLERANCE = Decimal('0.01')


class PaymentStatusError(Exception):
    """Raised when a payment status does not match contract totals."""


def get_contract_for_payment_check(contract: DbContract) -> DbContract:
    """Always validate against current DB rows (partials, extras, elevators)."""
    if contract.pk is None:
        return contract
    return DbContract.objects.prefetch_related(
        'elevators', 'extra', 'discount', 'partial'
    ).get(pk=contract.pk)


def compute_contract_totals(contract: DbContract) -> dict[str, float]:
    contract = get_contract_for_payment_check(contract)
    base_amount = sum(elevator.Total for elevator in contract.elevators.all())
    # Legacy support:
    # - if percentage fields exist/are filled, we compute deterministic percent effects.
    # - otherwise we fall back to numeric money fields.

    extras = list(contract.extra.all())
    discounts = list(contract.discount.all())

    has_any_extra_percentage = any(getattr(e, 'percentage', None) not in (None, '') for e in extras)
    has_any_discount_percentage = any(getattr(d, 'percentage', None) not in (None, '') for d in discounts)

    if not (has_any_extra_percentage or has_any_discount_percentage):
        total_extra = sum(extra.money for extra in extras)
        total_discount = sum(discount.discount_money for discount in discounts)
        net_total = float(base_amount + total_extra - total_discount)
    else:
        # Percent on running net total, deterministic:
        # base -> apply extras percents in queryset order -> apply discounts percents in queryset order.
        net = float(base_amount)

        for extra in extras:
            pct = getattr(extra, 'percentage', None)
            if pct in (None, ''):
                continue
            net += (net * float(pct) / 100.0)

        for discount in discounts:
            pct = getattr(discount, 'percentage', None)
            if pct in (None, ''):
                continue
            net -= (net * float(pct) / 100.0)

        net_total = net

    amount_paid = float(sum(payment.amount for payment in contract.partial.all()))
    balance_due = net_total - amount_paid

    # keep backward-compatible naming; also expose percent-derived amounts

    # expose legacy-compatible keys (some UI reads net_total/amount_paid/balance_due only)
    return {
        'net_total': net_total,
        'amount_paid': amount_paid,
        'balance_due': balance_due,
        'has_partial_records': contract.partial.exists(),
    }



def infer_payment_status(net_total: float, amount_paid: float, balance_due: float) -> int:
    """Derive the correct ContratE value from financial totals."""
    if balance_due <= float(TOLERANCE):
        if amount_paid > float(TOLERANCE) or net_total <= float(TOLERANCE):
            return ContratE.TWO
        return ContratE.ONE
    if amount_paid > float(TOLERANCE):
        return ContratE.THREE
    return ContratE.ONE


def get_payment_status_constraints(contract: DbContract) -> dict:
    """UI + API flags for which statuses are allowed."""
    totals = compute_contract_totals(contract)
    paid = totals['amount_paid']
    balance = totals['balance_due']
    net = totals['net_total']
    tol = float(TOLERANCE)

    can_mark_not_paid = paid <= tol
    can_mark_fully_paid = balance <= tol
    can_mark_partial_paid = paid > tol and balance > tol

    allowed = []
    if can_mark_not_paid:
        allowed.append(ContratE.ONE)
    if can_mark_fully_paid:
        allowed.append(ContratE.TWO)
    if can_mark_partial_paid:
        allowed.append(ContratE.THREE)

    return {
        **totals,
        'can_mark_not_paid': can_mark_not_paid,
        'can_mark_fully_paid': can_mark_fully_paid,
        'can_mark_partial_paid': can_mark_partial_paid,
        'allowed_statuses': allowed,
        'inferred_status': infer_payment_status(net, paid, balance),
    }


def validate_payment_status_change(contract: DbContract, new_status: int) -> dict[str, float]:
    """Raise PaymentStatusError if new_status conflicts with recorded payments."""
    new_status = int(new_status)
    if new_status not in (ContratE.ONE, ContratE.TWO, ContratE.THREE):
        raise PaymentStatusError('Invalid payment status.')

    contract = get_contract_for_payment_check(contract)
    constraints = get_payment_status_constraints(contract)

    if new_status not in constraints['allowed_statuses']:
        if new_status == ContratE.ONE:
            raise PaymentStatusError(
                f'Cannot mark as Not paid: ETB {constraints["amount_paid"]:,.2f} '
                f'has already been paid on this contract.'
            )
        if new_status == ContratE.TWO:
            raise PaymentStatusError(
                f'Cannot mark as Fully paid: ETB {constraints["balance_due"]:,.2f} '
                f'is still expected (paid ETB {constraints["amount_paid"]:,.2f} '
                f'of ETB {constraints["net_total"]:,.2f}).'
            )
        if new_status == ContratE.THREE:
            if constraints['amount_paid'] <= float(TOLERANCE):
                raise PaymentStatusError(
                    'Cannot mark as Partial paid: no partial payments recorded.'
                )
            raise PaymentStatusError(
                'Cannot mark as Partial paid: the contract balance is already settled.'
            )

    return constraints


def sync_contract_payment_status(contract: DbContract, *, save: bool = True) -> tuple[int, dict[str, float]]:
    """Set payed from current totals (after payments, extras, or discounts change)."""
    contract = get_contract_for_payment_check(contract)
    constraints = get_payment_status_constraints(contract)
    new_status = constraints['inferred_status']
    if contract.payed != new_status:
        contract.payed = new_status
        if save:
            contract.save(update_fields=['payed'])
    return new_status, constraints


def set_payment_status(contract: DbContract, new_status: int, *, save: bool = True) -> DbContract:
    """Apply a user-chosen status only if it matches financial reality."""
    contract = get_contract_for_payment_check(contract)
    validate_payment_status_change(contract, new_status)
    contract.payed = int(new_status)
    if save:
        contract.save(update_fields=['payed'])
    return contract


def resync_contract_payment_status(contract_id: int) -> tuple[int, dict[str, float]]:
    contract = DbContract.objects.get(pk=contract_id)
    return sync_contract_payment_status(contract)
