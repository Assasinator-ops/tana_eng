from rest_framework import serializers
from TanaApp.models import DbElevator, DbWarranty


class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = DbWarranty
        fields = '__all__'


class ElevatorSerializer(serializers.ModelSerializer):
    # warranty = WarrantySerializer(read_only=True)
    warranty = WarrantySerializer(many=True, read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)

    class Meta:
        model = DbElevator
        # fields = '__all__' + ['building_name']
        fields = [
            'id', 'commissionnumber', 'name', 'model',
            'number_of_stops', 'landing_door_unit', 'landing_door_quantity',
            'drive_unit', 'drive_quantity', 'car', 'car_quantity',
            'shaft_pit', 'shaft_quantity', 'Total',
            'registerd_date', 'started_date', 'building', 'building_name', 'warranty'
        ]

        extra_kwargs = {
            'Total': {'read_only': True}  # Calculated field
        }

    def create(self, validated_data):
        # Calculate Total
        validated_data['Total'] = (
                (validated_data['landing_door_unit'] * validated_data['landing_door_quantity']) +
                (validated_data['drive_unit'] * validated_data['drive_quantity']) +
                (validated_data['car'] * validated_data['car_quantity']) +
                (validated_data['shaft_pit'] * validated_data['shaft_quantity'])
        )
        return super().create(validated_data)

class ElevatorToContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbElevator
        fields = ['id', 'name', 'Total']
