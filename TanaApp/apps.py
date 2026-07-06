import os

from django.apps import AppConfig


class TanaappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TanaApp'

    def ready(self):
        # Connect signal handlers (contract <-> elevator M2M, elevator
        # create/update/delete, extras/discounts/partials).
        # Imported here to avoid AppRegistryNotReady errors.
        from . import signals  # noqa: F401

        # Start the background contract-total auditor (30 min cadence).
        # Skip during management commands like migrate/makemigrations so
        # we don't spawn threads for one-shot CLI work.
        import sys
        cmd = sys.argv[1] if len(sys.argv) > 1 else ''
        skip_commands = {
            'migrate', 'makemigrations', 'collectstatic', 'test',
            'shell', 'createsuperuser', 'check', 'showmigrations',
            'dbshell', 'sqlmigrate', 'audit_contract_totals',
        }
        run_main = (os.environ.get('RUN_MAIN') == 'true') or 'runserver' not in sys.argv
        if cmd in skip_commands:
            return
        # When using ``runserver``, Django spawns a reloader child; only
        # start the auditor in the parent process (``RUN_MAIN=true``) or
        # when not running under the autoreloader (gunicorn / wsgi).
        from TanaApp.audit import ContractTotalAuditor
        if 'runserver' in sys.argv and not run_main:
            return
        ContractTotalAuditor.get().start()
