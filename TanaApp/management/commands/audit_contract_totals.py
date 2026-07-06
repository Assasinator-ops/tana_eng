"""Recompute and correct every contract's net total right now.

Usage::

    python manage.py audit_contract_totals            # one-shot, prints stats
    python manage.py audit_contract_totals --quiet    # less output

Returns a non-zero exit code if any contract had to be corrected, so
the command can be wired into cron / health checks.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from TanaApp.audit import ContractTotalAuditor


class Command(BaseCommand):
    help = 'Recompute and correct every contract\'s net total (audit job).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet', action='store_true', help='Only print the final stats line.',
        )

    def handle(self, *args, **options):
        auditor = ContractTotalAuditor.get()
        stats = auditor.run_once(reason_label='Manual audit (management command)')

        if options.get('quiet'):
            self.stdout.write(str(stats))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Audit complete: scanned={stats['scanned']} "
            f"corrected={stats['corrected']} unchanged={stats['unchanged']} "
            f"in {stats['duration_ms']}ms"
        ))
        if stats['corrected']:
            # Non-zero exit code so CI / monitoring can detect drift.
            raise SystemExit(2)
