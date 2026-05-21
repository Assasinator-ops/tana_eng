from rest_framework import serializers
from TanaApp.models import DbBuilding, DbElevator, DbContract, DbWarranty

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbBuilding
        fields = '__all__'
        extra_kwargs = {
            'phone2': {'required': False, 'allow_null': True},
            'phone3': {'required': False, 'allow_null': True},
            'email2': {'required': False, 'allow_null': True}
        }

class BuildingCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    phone1 = serializers.CharField()
    phone2 = serializers.CharField(allow_null=True)
    phone3 = serializers.CharField(allow_null=True)
    email1 = serializers.CharField()
    owner_name = serializers.CharField(source='owner.name')

class ElevatorContractSerializer(serializers.Serializer):
    buildingname = serializers.CharField()
    commissionnumber = serializers.CharField()
    elevatorname = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()

class WarrantySerializer(serializers.Serializer):
    buildingname = serializers.CharField()
    commissionnumber = serializers.CharField()
    elevatorname = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()