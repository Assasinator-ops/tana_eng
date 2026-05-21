from rest_framework import serializers
from TanaApp.models import DbExtra

class ExtraSerializer(serializers.ModelSerializer):
    money = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = DbExtra
        fields = '__all__'
        extra_kwargs = {
            'discription': {'required': False},  # Note preserved typo
            'discription1': {'required': False},
            'money': {'required': False},
        }

    def validate(self, attrs):
        attrs.setdefault('money', 0.0)
        return attrs


class ExtraManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbExtra
        fields = ['percentage', 'discription', 'discription1']
        extra_kwargs = {
            'discription': {'required': False},
            'discription1': {'required': False},
        }

