from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from TanaApp.models import DbElevatorExtra, DbElevatorDiscount, DbElevator
from TanaApp.contract_payment import compute_contract_totals


def _q2(raw: float) -> float:
    return float(Decimal(str(raw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


class ElevatorExtraSerializer(serializers.ModelSerializer):
    money = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = DbElevatorExtra
        fields = ['id', 'elevator', 'time', 'money', 'percentage', 'discription', 'discription1']
        read_only_fields = ['id', 'time', 'elevator']

    def validate(self, attrs):
        attrs.setdefault('money', 0.0)
        return attrs


class ElevatorExtraManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbElevatorExtra
        fields = ['id', 'money', 'percentage', 'discription', 'discription1']
        extra_kwargs = {
            'money': {'required': False},
            'percentage': {'required': False},
            'discription': {'required': False},
            'discription1': {'required': False},
        }

    def validate(self, attrs):
        money = attrs.get('money', None)
        pct = attrs.get('percentage', None)

        # Normalize blanks -> None
        if money in ('',):
            money = None
        if pct in ('',):
            pct = None

        if money is None and pct is None:
            attrs['money'] = 0.0
            attrs['percentage'] = 0.0
        return attrs

    def _compute_money_from_pct(self, *, elevator: DbElevator, pct: float) -> float:
        base = float(elevator.Total or 0)
        if base == 0:
            return 0.0
        return _q2(base * float(pct) / 100.0)

    def _compute_pct_from_money(self, *, elevator: DbElevator, money: float) -> float:
        base = float(elevator.Total or 0)
        if base == 0:
            return 0.0
        return float(money) / base * 100.0

    def create(self, validated_data):
        request = self.context.get('request')
        elevator_id = self.context.get('elevator_id')
        elevator = DbElevator.objects.get(id=elevator_id)

        pct = validated_data.get('percentage', None)
        money = validated_data.get('money', None)

        if pct in ('',):
            pct = None
        if money in ('',):
            money = None

        if money is None and pct is not None:
            validated_data['money'] = self._compute_money_from_pct(elevator=elevator, pct=float(pct))
        elif pct is None and money is not None:
            validated_data['percentage'] = self._compute_pct_from_money(elevator=elevator, money=float(money))
        elif pct is None and money is None:
            validated_data['money'] = 0.0
            validated_data['percentage'] = 0.0

        return DbElevatorExtra.objects.create(elevator=elevator, **validated_data)

    def update(self, instance, validated_data):
        elevator = instance.elevator

        pct = validated_data.get('percentage', instance.percentage)
        money = validated_data.get('money', instance.money)

        if pct in ('',):
            pct = None
        if money in ('',):
            money = None

        if money is None and pct is not None:
            validated_data['money'] = self._compute_money_from_pct(elevator=elevator, pct=float(pct))
        elif pct is None and money is not None:
            validated_data['percentage'] = self._compute_pct_from_money(elevator=elevator, money=float(money))
        elif pct is None and money is None:
            validated_data['money'] = 0.0
            validated_data['percentage'] = 0.0

        return super().update(instance, validated_data)


class ElevatorDiscountSerializer(serializers.ModelSerializer):
    discount_money = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = DbElevatorDiscount
        fields = ['id', 'elevator', 'time', 'discount_money', 'percentage', 'description', 'description2']
        read_only_fields = ['id', 'time', 'elevator']

    def validate(self, attrs):
        attrs.setdefault('discount_money', 0.0)
        return attrs


class ElevatorDiscountManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbElevatorDiscount
        fields = ['id', 'discount_money', 'percentage', 'description', 'description2']
        extra_kwargs = {
            'discount_money': {'required': False},
            'percentage': {'required': False},
            'description': {'required': False},
            'description2': {'required': False},
        }

    def validate(self, attrs):
        dm = attrs.get('discount_money', None)
        pct = attrs.get('percentage', None)

        if dm in ('',):
            dm = None
        if pct in ('',):
            pct = None

        if dm is None and pct is None:
            attrs['discount_money'] = 0.0
            attrs['percentage'] = 0.0
        return attrs

    def _compute_dm_from_pct(self, *, elevator: DbElevator, pct: float) -> float:
        base = float(elevator.Total or 0)
        if base == 0:
            return 0.0
        return _q2(base * float(pct) / 100.0)

    def _compute_pct_from_dm(self, *, elevator: DbElevator, dm: float) -> float:
        base = float(elevator.Total or 0)
        if base == 0:
            return 0.0
        return float(dm) / base * 100.0

    def create(self, validated_data):
        elevator_id = self.context.get('elevator_id')
        elevator = DbElevator.objects.get(id=elevator_id)

        pct = validated_data.get('percentage', None)
        dm = validated_data.get('discount_money', None)

        if pct in ('',):
            pct = None
        if dm in ('',):
            dm = None

        if dm is None and pct is not None:
            validated_data['discount_money'] = self._compute_dm_from_pct(elevator=elevator, pct=float(pct))
        elif pct is None and dm is not None:
            validated_data['percentage'] = self._compute_pct_from_dm(elevator=elevator, dm=float(dm))
        elif pct is None and dm is None:
            validated_data['discount_money'] = 0.0
            validated_data['percentage'] = 0.0

        return DbElevatorDiscount.objects.create(elevator=elevator, **validated_data)

    def update(self, instance, validated_data):
        elevator = instance.elevator

        pct = validated_data.get('percentage', instance.percentage)
        dm = validated_data.get('discount_money', instance.discount_money)

        if pct in ('',):
            pct = None
        if dm in ('',):
            dm = None

        if dm is None and pct is not None:
            validated_data['discount_money'] = self._compute_dm_from_pct(elevator=elevator, pct=float(pct))
        elif pct is None and dm is not None:
            validated_data['percentage'] = self._compute_pct_from_dm(elevator=elevator, dm=float(dm))
        elif pct is None and dm is None:
            validated_data['discount_money'] = 0.0
            validated_data['percentage'] = 0.0

        return super().update(instance, validated_data)

