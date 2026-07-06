"""
Database logging handler for Django
"""
import logging
from django.conf import settings


class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes log entries to the database.
    """
    def __init__(self):
        super().__init__()
        self.level_map = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL',
        }

    def emit(self, record):
        try:
            # Import here to avoid circular dependency during settings loading
            from .models import AuditLog
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user from record if available (set by middleware)
            user = getattr(record, 'user', None)
            
            # Get IP address from record if available
            ip_address = getattr(record, 'ip_address', None)
            
            # Get user agent from record if available
            user_agent = getattr(record, 'user_agent', None)
            
            # Create audit log entry
            AuditLog.objects.create(
                level=self.level_map.get(record.levelno, 'INFO'),
                user=user,
                action=record.name or 'general',
                model_name=getattr(record, 'model_name', None),
                object_id=str(getattr(record, 'object_id', '')) if hasattr(record, 'object_id') else None,
                message=self.format(record),
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data={
                    'function': record.funcName,
                    'line': record.lineno,
                    'module': record.module,
                } if hasattr(record, 'funcName') else None
            )
        except Exception:
            # Don't raise exceptions in logging to prevent infinite loops
            self.handleError(record)


def setup_database_logging():
    """
    Configure Django logging to use database handler.
    """
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'database': {
                'level': 'INFO',
                'class': 'TanaApp.logging.DatabaseLogHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['database', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'TanaApp': {
                'handlers': ['database', 'console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }
    return LOGGING
