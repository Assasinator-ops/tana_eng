from rest_framework import serializers
from TanaApp.models import DbElevator, DbWarranty
from TanaApp.contract_payment import (
    compute_elevator_total,
    recompute_and_persist_contract_total,
)
from TanaApp.models import TotalCorrectionLog


def _recompute_contracts_for_elevator(elevator, *, reason, detail):
    """For every contract this elevator is attached to, recompute the total."""
    for contract in elevator.contracts.all():
        recompute_and_persist_contract_total(
            contract, reason=reason, detail=detail, notify=True,
        )


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

    @staticmethod
    def _compute_total_from(validated_data):
        return compute_elevator_total(
            landing_door_unit=validated_data.get('landing_door_unit', 0),
            landing_door_quantity=validated_data.get('landing_door_quantity', 0),
            drive_unit=validated_data.get('drive_unit', 0),
            drive_quantity=validated_data.get('drive_quantity', 0),
            car=validated_data.get('car', 0),
            car_quantity=validated_data.get('car_quantity', 0),
            shaft_pit=validated_data.get('shaft_pit', 0),
            shaft_quantity=validated_data.get('shaft_quantity', 0),
        )

    def create(self, validated_data):
        # Use the canonical quantized calculator (2 dp, ROUND_HALF_UP).
        validated_data['Total'] = self._compute_total_from(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Recompute Total from the (new) components every time we PATCH/PUT.
        if any(k in validated_data for k in (
            'landing_door_unit', 'landing_door_quantity',
            'drive_unit', 'drive_quantity',
            'car', 'car_quantity',
            'shaft_pit', 'shaft_quantity',
        )):
            merged = {**{
                'landing_door_unit': instance.landing_door_unit,
                'landing_door_quantity': instance.landing_door_quantity,
                'drive_unit': instance.drive_unit,
                'drive_quantity': instance.drive_quantity,
                'car': instance.car,
                'car_quantity': instance.car_quantity,
                'shaft_pit': instance.shaft_pit,
                'shaft_quantity': instance.shaft_quantity,
            }, **validated_data}
            validated_data['Total'] = self._compute_total_from(merged)
        elevator = super().update(instance, validated_data)

        # After persisting the elevator's own Total, every contract that
        # has this elevator attached needs its net total refreshed. We do
        # this here (in addition to the M2M signal) so price updates on
        # the elevator page also propagate.
        _recompute_contracts_for_elevator(
            elevator,
            reason=TotalCorrectionLog.REASON_ELEVATOR_CHANGED,
            detail=f'Elevator "{elevator.name}" (#{elevator.id}) updated.',
        )
        return elevator


class ElevatorToContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbElevator
        fields = ['id', 'name', 'Total']
