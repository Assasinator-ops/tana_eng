from rest_framework import serializers
from TanaApp.models import DbExpense

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbExpense
        fields = '__all__'
        extra_kwargs = {
            'total': {'required': False, 'allow_null': True}
        }