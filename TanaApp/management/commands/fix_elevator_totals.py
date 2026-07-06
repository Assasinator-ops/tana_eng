"""
Management command to fix elevator Total fields that may have incorrect values.

This command recalculates the Total field for every elevator using the canonical
formula and updates the database if the current value is incorrect.

Usage:
    python manage.py fix_elevator_totals
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from TanaApp.models import DbElevator
from TanaApp.contract_payment import compute_elevator_total


class Command(BaseCommand):
    help = 'Recalculate and fix elevator Total fields for all elevators'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing anything',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        elevators = DbElevator.objects.all()
        total_count = elevators.count()
        fixed_count = 0
        unchanged_count = 0

        self.stdout.write(f'Scanning {total_count} elevators...')

        for elevator in elevators:
            # Calculate the correct total
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
                self.stdout.write(
                    self.style.WARNING(
                        f'Elevator #{elevator.id} ({elevator.name}): '
                        f'Current={elevator.Total}, Correct={correct_total}'
                    )
                )
                if not dry_run:
                    elevator.Total = correct_total
                    elevator.save(update_fields=['Total'])
                fixed_count += 1
            else:
                unchanged_count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} elevator totals'))

        self.stdout.write(
            f'Total: {total_count}, Fixed: {fixed_count}, Unchanged: {unchanged_count}'
        )
