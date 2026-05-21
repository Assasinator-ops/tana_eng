from rest_framework import serializers
from TanaApp.models import DBPartialPyment, DbContract


class PartialPaymentSerializer(serializers.ModelSerializer):
    contract = serializers.PrimaryKeyRelatedField(
        queryset=DbContract.objects.select_related('building').order_by('-id'),
    )

    class Meta:
        model = DBPartialPyment
        fields = '__all__'


class PartialPaymentManageSerializer(serializers.ModelSerializer):
    """Manage-page form: contract is implicit from the URL."""

    class Meta:
        model = DBPartialPyment
        fields = ['amount', 'total']
        extra_kwargs = {
            'amount': {'help_text': 'Payment amount to add'},
            'total': {'help_text': 'Full contract amount due (base + extras − discounts)'},
        }