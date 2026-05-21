from rest_framework import serializers
from TanaApp.models import DbOwner

class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbOwner
        fields = '__all__'
        read_only_fields = ['id']
        extra_kwargs = {
            'phone2': {'allow_null': True, 'required': False},
            'address': {'required': False}
        }