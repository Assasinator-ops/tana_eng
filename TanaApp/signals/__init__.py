"""Django signals for the TanaApp.

The single most important signal here is `m2m_changed` on
`DbContract.elevators`: whenever an elevator is attached or detached
from a contract (the AddElevatorToContract flow, the bulk attach, or
admin actions), we need to recompute the contract's net total.

Elevators also fire `post_save` / `post_delete` so the contract picks
up new or removed price components.
"""
from __future__ import annotations

import logging

from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver

from TanaApp.models import (
    DbContract,
    DbElevator,
    DbDiscount,
    DbExtra,
    DBPartialPyment,
    TotalCorrectionLog,
)
from TanaApp.contract_payment import recompute_and_persist_contract_total

logger = logging.getLogger(__name__)


def _recompute(contract, *, reason: str, detail: str) -> None:
    try:
        recompute_and_persist_contract_total(
            contract, reason=reason, detail=detail, notify=True,
        )
    except Exception:
        logger.exception('Failed to recompute contract %s after %s', contract.id, reason)


@receiver(m2m_changed, sender=DbContract.elevators.through)
def contract_elevators_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """An elevator was added/removed/cleared from a contract.

    We care about the *forward* relation (instance is a contract) for
    `post_add` and `post_remove`/`post_clear`. The reverse direction
    (managing the relation from the elevator side) is also handled by
    iterating affected contracts.
    """
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    if not reverse:
        # instance is a DbContract
        contracts = [instance]
    else:
        # instance is a DbElevator; pk_set contains affected contract ids
        contract_ids = pk_set or set()
        contracts = list(DbContract.objects.filter(pk__in=contract_ids))

    for contract in contracts:
        if action == 'post_add':
            detail = f'Elevator(s) attached to contract #{contract.id}.'
        elif action == 'post_remove':
            detail = f'Elevator(s) removed from contract #{contract.id}.'
        else:
            detail = f'All elevators cleared from contract #{contract.id}.'
        _recompute(
            contract,
            reason=TotalCorrectionLog.REASON_CONTRACT_CHANGED,
            detail=detail,
        )


@receiver(post_save, sender=DbElevator)
def elevator_saved(sender, instance, created, **kwargs):
    if created:
        return  # nothing to recompute: elevator isn't attached anywhere yet
    # When an elevator's price components change, recompute every contract
    # that includes it. (The serializer also does this for DRF PATCH/PUT,
    # but signals cover direct ORM/admin updates too.)
    for contract in instance.contracts.all():
        _recompute(
            contract,
            reason=TotalCorrectionLog.REASON_ELEVATOR_CHANGED,
            detail=f'Elevator "{instance.name}" (#{instance.id}) updated.',
        )


@receiver(post_delete, sender=DbElevator)
def elevator_deleted(sender, instance, **kwargs):
    for contract in list(instance.contracts.all()):
        _recompute(
            contract,
            reason=TotalCorrectionLog.REASON_ELEVATOR_CHANGED,
            detail=f'Elevator "{instance.name}" (#{instance.id}) removed.',
        )


# ---------------------------------------------------------------------------
# Contract create -> ensure a DbTotal row exists
# ---------------------------------------------------------------------------
@receiver(post_save, sender=DbContract)
def contract_saved(sender, instance, created, **kwargs):
    # Only seed an initial total on create. Subsequent edits to contract
    # fields (start_date, end_date) don't change money, so we don't
    # touch the total here. (Elevator attach is handled by the m2m signal.)
    if created:
        try:
            recompute_and_persist_contract_total(
                instance,
                reason=TotalCorrectionLog.REASON_CONTRACT_CHANGED,
                detail=f'Contract #{instance.id} created.',
                notify=True,
            )
        except Exception:
            logger.exception('Failed to seed total for new contract %s', instance.id)


# ---------------------------------------------------------------------------
# Extras / Discounts / Partial payments -> recompute the parent contract
# ---------------------------------------------------------------------------
def _on_finance_change(instance, reason: str, label: str):
    contract_id = getattr(instance, 'contract_id', None)
    if not contract_id:
        return
    try:
        contract = DbContract.objects.get(pk=contract_id)
    except DbContract.DoesNotExist:
        return
    _recompute(
        contract,
        reason=reason,
        detail=f'{label} #{getattr(instance, "id", "?")} on contract #{contract.id}.',
    )


@receiver(post_save, sender=DbExtra)
def extra_saved(sender, instance, created, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_EXTRAS_CHANGED,
        'Extra',
    )


@receiver(post_delete, sender=DbExtra)
def extra_deleted(sender, instance, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_EXTRAS_CHANGED,
        'Extra',
    )


@receiver(post_save, sender=DbDiscount)
def discount_saved(sender, instance, created, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_DISCOUNTS_CHANGED,
        'Discount',
    )


@receiver(post_delete, sender=DbDiscount)
def discount_deleted(sender, instance, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_DISCOUNTS_CHANGED,
        'Discount',
    )


@receiver(post_save, sender=DBPartialPyment)
def partial_saved(sender, instance, created, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_PARTIAL_CHANGED,
        'Partial payment',
    )


@receiver(post_delete, sender=DBPartialPyment)
def partial_deleted(sender, instance, **kwargs):
    _on_finance_change(
        instance,
        TotalCorrectionLog.REASON_PARTIAL_CHANGED,
        'Partial payment',
    )
