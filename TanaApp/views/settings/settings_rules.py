# Supported currencies (ISO 4217)
CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY",
    "SEK", "NZD", "MXN", "SGD", "HKD", "NOK", "KRW", "INR"
]

# Notification levels
NOTIFICATION_LEVELS = ["none", "low", "medium", "high"]

# Timezone validation (simplified)
def is_valid_timezone(tz):
    import pytz
    return tz in pytz.all_timezones

# Language codes
LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ru", "Russian"),
    ("ar", "Arabic")
]