"""
Contract payment status rules tied to calculator totals (expected vs paid).

This module is the **single source of truth** for contract money math:

* `compute_contract_totals(contract)` -> {net_total, amount_paid, balance_due, ...}
* `recompute_and_persist_contract_total(contract, *, reason, detail)` will:
    - recompute the totals,
    - upsert the legacy `DbTotal` row so the calculator endpoint agrees,
    - write a `TotalCorrectionLog` audit row,
    - create a `DbMessage` so the notifications feed shows the change.

All money is quantized to 2 decimals with ROUND_HALF_UP so two
contracts with the same inputs always produce the same total and a
company can never lose a single cent to a float rounding bug.
"""
from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from TanaApp.models import (
    ContratE,
    DbContract,
    DbTotal,
    TotalCorrectionLog,
    DbMessage,
    DbUser,
)

logger = logging.getLogger(__name__)

TOLERANCE = Decimal('0.01')
CENTS = Decimal('0.01')


def _q(value) -> Decimal:
    """Quantize a numeric value to 2 decimals using ROUND_HALF_UP."""
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def _to_float(d: Decimal) -> float:
    return float(d)


class PaymentStatusError(Exception):
    """Raised when a payment status does not match contract totals."""


def get_contract_for_payment_check(contract: DbContract) -> DbContract:
    """Always validate against current DB rows (partials, extras, elevators)."""
    if contract.pk is None:
        return contract
    return DbContract.objects.prefetch_related(
        'elevators', 'extra', 'discount', 'partial'
    ).get(pk=contract.pk)


# ---------------------------------------------------------------------------
# Elevator-side helpers
# ---------------------------------------------------------------------------
def compute_elevator_total(*, landing_door_unit=0, landing_door_quantity=0,
                            drive_unit=0, drive_quantity=0,
                            car=0, car_quantity=0,
                            shaft_pit=0, shaft_quantity=0) -> float:
    """Deterministic, quantized sum of all elevator price components.

    Formula: (landing_door_unit * landing_door_quantity) +
             (drive_unit * drive_quantity) +
             (car * car_quantity) +
             (shaft_pit * shaft_quantity)
    """
    raw = (
        (Decimal(str(landing_door_unit or 0)) * Decimal(str(landing_door_quantity or 0))) +
        (Decimal(str(drive_unit or 0)) * Decimal(str(drive_quantity or 0))) +
        (Decimal(str(car or 0)) * Decimal(str(car_quantity or 0))) +
        (Decimal(str(shaft_pit or 0)) * Decimal(str(shaft_quantity or 0)))
    )
    return _to_float(_q(raw))


def compute_elevator_invoice(elevator, extras=None, discounts=None, vat_rate=0.15) -> dict:
    """Calculate complete invoice breakdown for a single elevator.

    Args:
        elevator: DbElevator instance
        extras: List of extra amounts (float) or None
        discounts: List of discount amounts (float) or None
        vat_rate: VAT percentage (default 15%)

    Returns:
        dict with complete breakdown including VAT, term totals, and discounts
    """
    base_total = _q(Decimal(str(elevator.Total)))
    
    # VAT calculation on base total first
    vat_amount_base = _q(base_total * Decimal(str(vat_rate)))
    base_total_with_vat = _q(base_total + vat_amount_base)
    
    # Add extras (calculated from after-VAT base)
    extras_total = Decimal('0.00')
    if extras:
        extras_total = _q(sum(Decimal(str(e or 0)) for e in extras))
    
    subtotal_after_extras = _q(base_total_with_vat + extras_total)
    
    # Apply discounts (calculated from after-VAT+extras)
    discounts_total = Decimal('0.00')
    if discounts:
        discounts_total = _q(sum(Decimal(str(d or 0)) for d in discounts))
    
    subtotal = _q(subtotal_after_extras - discounts_total)
    
    # Total VAT (VAT on base only, extras/discounts are already after-VAT amounts)
    total_vat_amount = vat_amount_base
    
    total_with_vat = _q(subtotal)
    
    # Term calculations (total_with_vat is the monthly amount)
    monthly = total_with_vat
    quarterly = _q(monthly * Decimal('3'))
    annual = _q(monthly * Decimal('12'))
    
    # Term-based discounts
    semi_annual_discount = _q(annual * Decimal('0.01'))  # 1% discount
    semi_annual_total = _q(annual - semi_annual_discount)
    
    annual_discount = _q(annual * Decimal('0.03'))  # 3% discount
    annual_total = _q(annual - annual_discount)
    
    return {
        'base_total': _to_float(base_total),
        'base_total_with_vat': _to_float(base_total_with_vat),
        'extras_total': _to_float(extras_total),
        'discounts_total': _to_float(discounts_total),
        'subtotal': _to_float(subtotal),
        'vat_rate': vat_rate,
        'vat_amount': _to_float(total_vat_amount),
        'total_with_vat': _to_float(total_with_vat),
        'monthly': _to_float(monthly),
        'quarterly': _to_float(quarterly),
        'annual': _to_float(annual),
        'semi_annual_discount': _to_float(semi_annual_discount),
        'semi_annual_total': _to_float(semi_annual_total),
        'annual_discount': _to_float(annual_discount),
        'annual_total': _to_float(annual_total),
    }


# ---------------------------------------------------------------------------
# Contract totals
# ---------------------------------------------------------------------------
def _legacy_money(extras, discounts) -> tuple[Decimal, Decimal]:
    return (
        sum((_q(getattr(e, 'money', 0) or 0) for e in extras), Decimal('0.00')),
        sum((_q(getattr(d, 'discount_money', 0) or 0) for d in discounts), Decimal('0.00')),
    )


def _percent_path(base: Decimal, extras, discounts) -> Decimal:
    """Apply extras' and discounts' percent on the running net total."""
    net = base
    for extra in extras:
        pct = getattr(extra, 'percentage', None)
        if pct in (None, ''):
            continue
        net = _q(net + (net * Decimal(str(pct)) / Decimal('100')))
    for discount in discounts:
        pct = getattr(discount, 'percentage', None)
        if pct in (None, ''):
            continue
        net = _q(net - (net * Decimal(str(pct)) / Decimal('100')))
    return net


def compute_contract_totals(contract: DbContract, vat_rate: float = 0.15) -> dict[str, float]:
    """Recompute the canonical money breakdown for a contract.

    The base amount is **always** the sum of every attached elevator's
    `Total` field, so contracts with multiple elevators correctly add
    them up. Extra percent fields take precedence over the legacy
    `money` field when set; the `money` field is then recomputed by the
    serializers to stay in sync.

    VAT is applied to the net total (base + extras - discounts) to get
    the final amount that customers actually pay.

    All values are quantized to 2 decimals.
    """
    contract = get_contract_for_payment_check(contract)

    base_amount = _q(
        sum((_q(getattr(e, 'Total', 0) or 0) for e in contract.elevators.all()),
            Decimal('0.00'))
    )

    extras = list(contract.extra.all())
    discounts = list(contract.discount.all())

    has_any_extra_percentage = any(getattr(e, 'percentage', None) not in (None, '') for e in extras)
    has_any_discount_percentage = any(getattr(d, 'percentage', None) not in (None, '') for d in discounts)

    if not (has_any_extra_percentage or has_any_discount_percentage):
        total_extra, total_discount = _legacy_money(extras, discounts)
        net_total_before_vat = _q(base_amount + total_extra - total_discount)
    else:
        net_total_before_vat = _percent_path(base_amount, extras, discounts)

    # Apply VAT to get the final net total
    vat_amount = _q(net_total_before_vat * Decimal(str(vat_rate)))
    net_total = _q(net_total_before_vat + vat_amount)

    amount_paid = _q(
        sum((_q(getattr(p, 'amount', 0) or 0) for p in contract.partial.all()),
            Decimal('0.00'))
    )
    balance_due = _q(net_total - amount_paid)

    return {
        'base_amount': _to_float(base_amount),
        'net_total_before_vat': _to_float(net_total_before_vat),
        'vat_amount': _to_float(vat_amount),
        'vat_rate': vat_rate,
        'net_total': _to_float(net_total),
        'amount_paid': _to_float(amount_paid),
        'balance_due': _to_float(balance_due),
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


# ---------------------------------------------------------------------------
# Persistence + audit + notification
# ---------------------------------------------------------------------------
def _find_first_user() -> Optional[DbUser]:
    """Pick a recipient for system-generated messages.

    Prefer the first admin (usertype=1) and fall back to any user. Returns
    None when no user exists yet.
    """
    user = DbUser.objects.filter(status=True, usertype=1).order_by('id').first()
    if user:
        return user
    user = DbUser.objects.filter(status=True).order_by('id').first()
    return user


def _emit_notification(*, contract: DbContract, reason: str,
                       previous_total: float, new_total: float,
                       detail: str) -> None:
    """Write a DbMessage so the change appears in the in-app notification feed."""
    user = _find_first_user()
    if user is None:
        return

    delta = _to_float(_q(Decimal(str(new_total)) - Decimal(str(previous_total or 0))))
    if abs(delta) < 0.005:
        arrow = '='
    elif delta > 0:
        arrow = 'UP'
    else:
        arrow = 'DOWN'
    title = f'Contract #{contract.id} total {arrow}'
    body = (
        f'{detail}\n'
        f'Previous: ETB {previous_total:,.2f}\n'
        f'New:      ETB {new_total:,.2f}\n'
        f'Delta:    ETB {delta:+,.2f}\n'
        f'Reason:   {reason}'
    )
    try:
        DbMessage.objects.create(
            title=title[:50],
            detail=body,
            employee=user,
        )
    except Exception:
        # Never let a notification failure break a money operation.
        logger.exception('Failed to write DbMessage for contract %s', contract.id)


def recompute_and_persist_contract_total(contract: DbContract, *,
                                          reason: str = TotalCorrectionLog.REASON_MANUAL,
                                          detail: str = '',
                                          notify: bool = True) -> dict[str, float]:
    """Recompute the contract net total, persist it in `DbTotal`, and log it.

    Returns the new totals dict. If the persisted `DbTotal.total` already
    matches the freshly-computed value (to the cent) the audit row is
    still written for traceability but no notification is fired unless
    `notify=True` and there is a real change.
    """
    totals = compute_contract_totals(contract)
    new_total = totals['net_total']

    # Read previous persisted total
    total_obj = DbTotal.objects.filter(contract=contract).order_by('id').first()
    previous_total = float(total_obj.total) if total_obj else None

    if total_obj is None:
        DbTotal.objects.create(contract=contract, total=new_total, is_Actiave=True)
    elif _q(total_obj.total) != _q(new_total):
        total_obj.total = new_total
        total_obj.is_Actiave = True
        total_obj.save(update_fields=['total', 'is_Actiave'])

    # Always write the log row so we have a full audit trail.
    delta = _to_float(_q(Decimal(str(new_total)) - Decimal(str(previous_total or 0))))
    try:
        TotalCorrectionLog.objects.create(
            contract=contract,
            reason=reason,
            previous_total=previous_total,
            new_total=new_total,
            delta=delta,
            detail=(detail or '')[:255],
        )
    except Exception:
        logger.exception('Failed to write TotalCorrectionLog for contract %s', contract.id)

    # Fire notification only when something actually changed (or first persist).
    changed = previous_total is None or _q(previous_total) != _q(new_total)
    if changed and notify:
        _emit_notification(
            contract=contract,
            reason=reason,
            previous_total=previous_total if previous_total is not None else 0.0,
            new_total=new_total,
            detail=detail or 'Contract total recomputed.',
        )

    return totals


def recompute_for_contracts(contract_ids: Iterable[int], *,
                             reason: str = TotalCorrectionLog.REASON_AUTO_AUDIT,
                             detail: str = '') -> dict[str, int]:
    """Recompute and persist totals for a batch of contracts.

    Returns a stats dict: {'scanned': N, 'corrected': M, 'unchanged': K}.
    """
    scanned = corrected = unchanged = 0
    for cid in contract_ids:
        try:
            contract = DbContract.objects.get(pk=cid)
        except DbContract.DoesNotExist:
            continue
        scanned += 1
        total_obj = DbTotal.objects.filter(contract=contract).order_by('id').first()
        previous_total = float(total_obj.total) if total_obj else None
        totals = recompute_and_persist_contract_total(
            contract, reason=reason,
            detail=detail or 'Scheduled audit run',
            notify=False,  # we fire one summary notification below only on real changes
        )
        if previous_total is not None and _q(previous_total) == _q(totals['net_total']):
            unchanged += 1
        else:
            corrected += 1
            # Per-contract notification so the user can see *which* contract moved.
            _emit_notification(
                contract=contract,
                reason=reason,
                previous_total=previous_total if previous_total is not None else 0.0,
                new_total=totals['net_total'],
                detail=detail or 'Auto-correction by background auditor.',
            )
    return {'scanned': scanned, 'corrected': corrected, 'unchanged': unchanged}
