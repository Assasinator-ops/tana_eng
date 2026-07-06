from rest_framework import serializers
from TanaApp.models import DbContract, DbElevator, DbBuilding, DBPartialPyment, DbExtra, DbTotal, TotalCorrectionLog
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from dateutil.relativedelta import relativedelta

from TanaApp.views.partial_payments.serializers import PartialPaymentSerializer
from TanaApp.contract_payment import (
    PaymentStatusError,
    validate_payment_status_change,
    get_contract_for_payment_check,
    compute_contract_totals,
    recompute_and_persist_contract_total,
)
from TanaApp.views.extras.serializers import ExtraSerializer
from TanaApp.views.discounts.serializers import DiscountSerializer

import logging

logger = logging.getLogger(__name__)

class ContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbContract
        exclude = ['elevators', 'building']
        extra_kwargs = {
            'payed': {'read_only': True},
            'end_date': {'read_only': True},
            'building': {'write_only': True, 'required': False}
        }

    @transaction.atomic
    def create(self, validated_data):
        # pop off any redirect hint
        redirect_to = validated_data.pop('next', None)
        print(redirect_to)
        # ✔️ Safely get building from either validated_data or context
        building = validated_data.pop('building', None)
        if not building:
            building_id = self.context.get('building')
            if not building_id:
                raise serializers.ValidationError("Missing building")
            try:
                building = DbBuilding.objects.get(id=building_id)
            except DbBuilding.DoesNotExist:
                raise serializers.ValidationError({"building": "Building with id {} does not exist.".format(building_id)})

        validated_data['building'] = building

        # compute end_date
        start = validated_data.get('start_date')
        paytime = validated_data.get('paytime', 0)
        logger.info(f"Contract creation - start_date: {start}, paytime: {paytime}")
        if start:
            validated_data['end_date'] = start + relativedelta(months=paytime)
            logger.info(f"Contract creation - calculated end_date: {validated_data['end_date']}")
        else:
            from django.utils import timezone
            validated_data['start_date'] = timezone.now()
            validated_data['end_date'] = timezone.now() + relativedelta(months=paytime)
            logger.info(f"Contract creation - calculated end_date (no start): {validated_data['end_date']}")

        # create the contract
        contract = super().create(validated_data)

        # Attach related records.
        # NOTE: We previously auto-created a placeholder DbDiscount with the
        # description 'no elevators attached' for every new contract. That row
        # surfaced in the manage page's discount list and had to be deleted by
        # hand. We no longer create it — contracts start with zero discounts,
        # and the UI hides any rows that match the legacy placeholder string.
        DBPartialPyment.objects.create(contract=contract, amount=0, total=0)

        # hint for redirect
        contract._redirect_to = redirect_to
        return contract

class ContractCalculatorSerializer(serializers.Serializer):
    base_amount = serializers.FloatField()
    net_total = serializers.FloatField()
    amount_paid = serializers.FloatField()
    balance_due = serializers.FloatField()

    # Used by UI to render the 1st “per elevator” section.
    # Each item: {id, name, model, Total}
    elevators = serializers.ListField(child=serializers.DictField())

    def to_representation(self, instance):
        contract = instance
        contract_date = contract.start_date

        partial_payments = [
            {'amount': payment.amount, 'date': payment.time}
            for payment in contract.partial.all()
        ]

        extra_charges = [
            {
                'money': extra.money,
                'description': extra.discription,
                'date': extra.time,
            }
            for extra in contract.extra.all()
        ]

        discounts = [
            {
                'discount_money': discount.discount_money,
                'description': discount.description,
                'date': discount.time,
            }
            for discount in contract.discount.all()
        ]

        # Use the canonical recompute (quantized to 2 dp, multi-elevator
        # aware, percent-aware) so calculator output matches what the
        # background auditor and total-write paths persist.
        totals = recompute_and_persist_contract_total(
            contract,
            reason=TotalCorrectionLog.REASON_MANUAL,
            detail='Calculator endpoint recomputed the contract total.',
            notify=True,
        )
        base_amount = totals['base_amount']
        net_total = totals['net_total']
        amount_paid = totals['amount_paid']
        balance_due = totals['balance_due']

        return {
            'base_amount': base_amount,
            'start_date': contract_date,
            'partial_payments': partial_payments,
            'extra_charges': extra_charges,
            'discounts': discounts,
            'net_total': net_total,
            'amount_paid': amount_paid,
            'balance_due': balance_due,
        }

class ElevatorBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbElevator
        fields = ['id', 'name', 'commissionnumber', 'Total']

class ContractSerializer(serializers.ModelSerializer):
    elevators = ElevatorBasicSerializer(many=True, read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)

    class Meta:
        model = DbContract
        fields = '__all__'


_DATETIME_INPUT_FORMATS = [
    'iso-8601',
    '%Y-%m-%dT%H:%M:%S.%fZ',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d',
    '%m/%d/%Y %I:%M %p',
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y',
]


class ContractUpdateSerializer(serializers.ModelSerializer):
    """PATCH/PUT from manage UI — contract fields only; elevators attached elsewhere."""

    start_date = serializers.DateTimeField(
        required=False, input_formats=_DATETIME_INPUT_FORMATS
    )
    end_date = serializers.DateTimeField(
        required=False, input_formats=_DATETIME_INPUT_FORMATS
    )

    class Meta:
        model = DbContract
        fields = ['id', 'start_date', 'end_date', 'paytime', 'payed']
        read_only_fields = ['id']
        extra_kwargs = {
            'paytime': {'required': False},
            'payed': {'required': False},
        }

    def _client_sent_end_date(self):
        raw = self.initial_data.get('end_date')
        return raw not in (None, '')

    def validate_payed(self, value):
        if self.instance is not None:
            try:
                contract = get_contract_for_payment_check(self.instance)
                validate_payment_status_change(contract, int(value))
            except PaymentStatusError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return int(value)

    def update(self, instance, validated_data):
        # Only auto-fill end_date when the client omitted it (e.g. API-only start/paytime patch).
        if not self._client_sent_end_date() and (
            'start_date' in validated_data or 'paytime' in validated_data
        ):
            start = validated_data.get('start_date', instance.start_date)
            paytime = validated_data.get('paytime', instance.paytime)
            logger.info(f"Contract update - start_date: {start}, paytime: {paytime}")
            validated_data['end_date'] = start + relativedelta(months=paytime)
            logger.info(f"Contract update - calculated end_date: {validated_data['end_date']}")

        return super().update(instance, validated_data)


class TotalSerializer(serializers.Serializer):
    Total = serializers.FloatField()
    eid = serializers.ListField(child=serializers.CharField())


class ExpiredContractSerializer(serializers.Serializer):
    startdate = serializers.DateTimeField()
    enddate = serializers.DateTimeField()
    elevatorname = serializers.CharField()
    elevatortotal = serializers.FloatField()
    buildingname = serializers.CharField()

class ContractManageSerializer(serializers.ModelSerializer):
    extras        = ExtraSerializer(many=True,   read_only=True, source='extra')
    discounts     = DiscountSerializer(many=True, read_only=True, source='discount')
    partial       = serializers.SerializerMethodField()
    partial_payments = serializers.SerializerMethodField()
    payed_display = serializers.CharField(source='get_payed_display', read_only=True)

    class Meta:
        model  = DbContract
        fields = [
            'id', 'start_date', 'end_date',
            'paytime','payed','payed_display',
            'extras','discounts','partial','partial_payments',
        ]

    def get_partial(self, obj):
        # Grab the first (or only) partial-payment record, if any
        pp_qs = obj.partial.all()           # this is a RelatedManager
        pp    = pp_qs.first()               # .first() returns None or a DBPartialPyment
        if not pp:
            return None
        return PartialPaymentSerializer(pp).data

    def get_partial_payments(self, obj):
        # Return all partial payment records
        pp_qs = obj.partial.all()
        return PartialPaymentSerializer(pp_qs, many=True).data