from rest_framework import serializers
from TanaApp.models import DbWarranty

class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = DbWarranty
        fields = '__all__'

class WarrantyExpirySerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    elevator_id = serializers.CharField()
    comission_Number = serializers.CharField()
    expired = serializers.BooleanField()

class ExpiredContractSerializer(serializers.Serializer):
    startdate = serializers.DateTimeField()
    enddate = serializers.DateTimeField()
    elevatorname = serializers.CharField()
    elevatortotal = serializers.FloatField()
    buildingname = serializers.CharField()