from rest_framework import serializers
from TanaApp.models import DbDiscount

class DiscountSerializer(serializers.ModelSerializer):
    discount_money = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = DbDiscount
        fields = '__all__'
        extra_kwargs = {
            'description2': {'required': False},
            'discount_money': {'required': False},
        }

    def validate(self, attrs):
        attrs.setdefault('discount_money', 0.0)
        return attrs


class DiscountManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbDiscount
        fields = ['discount_type', 'percentage', 'description', 'description2', 'carry']
        extra_kwargs = {
            'description2': {'required': False},
            'carry': {'required': False},
        }

