from rest_framework import serializers
from TanaApp.models import DbTimer

class TimerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbTimer
        fields = '__all__'
        read_only_fields = ['started', 'expire']
        extra_kwargs = {
            'discount': {'required': False},
            'extra': {'required': False},
            'expense': {'required': False}
        }