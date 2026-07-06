"""
Background auditor for contract totals.

Runs every ``AUDIT_INTERVAL_SECONDS`` (default 30 minutes) on a daemon
thread. The thread is started from ``TanaAppConfig.ready()`` and is
safe across Django's autoreload processes (it will only run in the
parent process).

Each tick:
  1. Walks every contract in the database.
  2. Recomputes the canonical net total via ``compute_contract_totals``.
  3. If the persisted ``DbTotal.total`` is off by more than 1 cent,
     the row is corrected, an audit row is written, and a
     ``DbMessage`` is sent so the user sees the change in the
     notification feed.

You can also trigger an immediate run via:
  - The management command ``python manage.py audit_contract_totals``
  - The HTTP endpoint ``POST /api/contracts/audit-totals/`` (auth required)
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

AUDIT_INTERVAL_SECONDS = 15 * 60  # 15 minutes


class ContractTotalAuditor:
    """Singleton-style daemon auditor."""

    _instance: Optional['ContractTotalAuditor'] = None
    _lock = threading.Lock()

    def __init__(self, interval_seconds: int = AUDIT_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_run_at = None
        self.last_stats: dict = {}

    @classmethod
    def get(cls) -> 'ContractTotalAuditor':
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_forever,
            name='contract-total-auditor',
            daemon=True,
        )
        self._thread.start()
        logger.info(
            'ContractTotalAuditor started (interval=%ss)', self.interval_seconds,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run_forever(self) -> None:
        # Run an initial audit a few seconds after boot so freshly-created
        # contracts catch up; then loop on the interval.
        time.sleep(5)
        while not self._stop_event.is_set():
            try:
                self.run_once()
                # Also audit elevator totals to catch any incorrect calculations
                self._audit_elevator_totals()
            except Exception:
                logger.exception('ContractTotalAuditor tick crashed')
            # Wait, but wake up promptly on stop.
            self._stop_event.wait(self.interval_seconds)

    def run_once(self, *, reason_label: str = 'Background audit') -> dict:
        """Recompute every contract's total and correct any drift.

        Returns a stats dict: {scanned, corrected, unchanged, duration_ms}.
        """
        from TanaApp.models import DbContract
        from TanaApp.contract_payment import recompute_for_contracts

        start = time.monotonic()
        contract_ids = list(DbContract.objects.values_list('id', flat=True))
        stats = recompute_for_contracts(
            contract_ids,
            reason='auto_audit',
            detail=reason_label,
        )
        stats['duration_ms'] = int((time.monotonic() - start) * 1000)
        stats['ran_at'] = timezone.now().isoformat()
        self.last_run_at = timezone.now()
        self.last_stats = stats
        logger.info(
            'ContractTotalAuditor: scanned=%s corrected=%s unchanged=%s in %sms',
            stats['scanned'], stats['corrected'], stats['unchanged'],
            stats['duration_ms'],
        )
        return stats

    def _audit_elevator_totals(self) -> dict:
        """Audit and fix elevator Total fields.

        Returns a stats dict: {scanned, corrected, unchanged, duration_ms}.
        """
        from TanaApp.models import DbElevator
        from TanaApp.contract_payment import compute_elevator_total

        start = time.monotonic()
        elevators = DbElevator.objects.all()
        scanned = corrected = unchanged = 0

        for elevator in elevators:
            scanned += 1
            correct_total = compute_elevator_total(
                landing_door_unit=elevator.landing_door_unit,
                landing_door_quantity=elevator.landing_door_quantity,
                drive_unit=elevator.drive_unit,
                drive_quantity=elevator.drive_quantity,
                car=elevator.car,
                car_quantity=elevator.car_quantity,
                shaft_pit=elevator.shaft_pit,
                shaft_quantity=elevator.shaft_quantity,
            )

            # Compare with current total (use string comparison to avoid float precision issues)
            if str(correct_total) != str(elevator.Total):
                elevator.Total = correct_total
                elevator.save(update_fields=['Total'])
                corrected += 1
                logger.info(
                    'Elevator total corrected: elevator_id=%s name=%s old=%s new=%s',
                    elevator.id, elevator.name, elevator.Total, correct_total
                )
            else:
                unchanged += 1

        stats = {
            'scanned': scanned,
            'corrected': corrected,
            'unchanged': unchanged,
            'duration_ms': int((time.monotonic() - start) * 1000),
        }
        if corrected > 0:
            logger.info(
                'Elevator total audit: scanned=%s corrected=%s unchanged=%s in %sms',
                stats['scanned'], stats['corrected'], stats['unchanged'],
                stats['duration_ms'],
            )
        return stats
