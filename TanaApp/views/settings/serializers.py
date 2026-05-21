from rest_framework import serializers
from TanaApp.models import GlobalSettings, PersonalizedSettings
from .settings_rules import CURRENCIES, NOTIFICATION_LEVELS, LANGUAGES, is_valid_timezone

class GlobalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSettings
        fields = '__all__'
        read_only_fields = ('id',)

    def validate_default_currency(self, value):
        if value not in CURRENCIES:
            raise serializers.ValidationError("Unsupported currency")
        return value

    def validate_default_timezone(self, value):
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value

class PersonalizedSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalizedSettings
        exclude = ('user',)
        read_only_fields = ('id',)

    def validate_preferred_language(self, value):
        if value not in [lang[0] for lang in LANGUAGES]:
            raise serializers.ValidationError("Unsupported language")
        return value

    def validate_timezone(self, value):
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value

    def validate_font_size(self, value):
        if not (12 <= value <= 24):
            raise serializers.ValidationError("Font size must be between 12-24px")
        return value