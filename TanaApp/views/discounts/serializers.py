from rest_framework import serializers
from TanaApp.models import DbDiscount
from decimal import Decimal, ROUND_HALF_UP

from TanaApp.contract_payment import compute_contract_totals





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

    # Contract manage page does not submit discount_type; DbDiscount requires it.
    # Provide a safe default so POST /api/discounts/contract/<id>/ works.
    discount_type = serializers.IntegerField(required=False, default=1)

    """Manage-page serializer for DbDiscount.


    Behavior:
    - If client sends percentage but not discount_money, compute discount_money from percentage.
    - If client sends discount_money (legacy), keep it.

    Rounding:
    - discount_money is rounded to 2 decimals using Decimal quantize.
    """

    class Meta:
        model = DbDiscount
        fields = ['discount_type', 'percentage', 'discount_money', 'description', 'description2', 'carry']
        extra_kwargs = {
            'description2': {'required': False},
            'carry': {'required': False},
            'discount_money': {'required': False},
            'percentage': {'required': False},
        }

    def validate(self, attrs):
        """Normalize null/blank and guarantee deterministic values.

        UI can send null for both percentage and discount_money. In that case we
        default to percentage=0 and discount_money=0 so calculator totals never break.
        """

        def _blank_to_none(v):
            if v in ('',):
                return None
            return v

        if 'discount_money' in attrs:
            attrs['discount_money'] = _blank_to_none(attrs['discount_money'])
        if 'percentage' in attrs:
            attrs['percentage'] = _blank_to_none(attrs['percentage'])

        money = attrs.get('discount_money', None)
        pct = attrs.get('percentage', None)

        if money is None and pct is None:
            attrs['percentage'] = 0.0
            attrs['discount_money'] = 0.0

        return attrs


    def _quantize_2(self, raw: float) -> float:
        return float(Decimal(str(raw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _compute_discount_delta(self, *, contract, pct: float) -> float:
        from TanaApp.contract_payment import compute_contract_totals

        totals_before = compute_contract_totals(contract)
        net_before = float(totals_before['net_total'])
        raw = net_before * float(pct) / 100.0
        return self._quantize_2(raw)

    def create(self, validated_data):
        contract_id = validated_data.pop('contract_id', None)
        if contract_id is None:
            raise serializers.ValidationError({'contract_id': 'This field is required.'})

        from TanaApp.models import DbContract
        contract = DbContract.objects.prefetch_related('elevators', 'extra', 'discount', 'partial').get(pk=contract_id)

        pct = validated_data.get('percentage', None)
        dm = validated_data.get('discount_money', None)

        if pct in ('',):
            pct = None
        if dm in ('',):
            dm = None

        if dm is None and pct is not None:
            validated_data['discount_money'] = self._compute_discount_delta(contract=contract, pct=float(pct))
        elif pct is None and dm is not None:
            totals_before = compute_contract_totals(contract)
            net_before = float(totals_before['net_total'])
            if net_before == 0:
                validated_data['percentage'] = 0.0
            else:
                validated_data['percentage'] = float(dm) / net_before * 100.0
        elif pct is None and dm is None:
            validated_data['percentage'] = 0.0
            validated_data['discount_money'] = 0.0

        return super().create({**validated_data, 'contract_id': contract_id})


    def update(self, instance, validated_data):
        contract = instance.contract

        pct = validated_data.get('percentage', getattr(instance, 'percentage', None))
        dm = validated_data.get('discount_money', None)

        if pct in ('',):
            pct = None
        if dm in ('',):
            dm = None

        if dm is None and pct is not None:
            validated_data['discount_money'] = self._compute_discount_delta(contract=contract, pct=float(pct))
        elif pct is None and dm is not None:
            totals_before = compute_contract_totals(contract)
            net_before = float(totals_before['net_total'])
            if net_before == 0:
                validated_data['percentage'] = 0.0
            else:
                validated_data['percentage'] = float(dm) / net_before * 100.0
        elif pct is None and dm is None:
            validated_data['percentage'] = 0.0
            validated_data['discount_money'] = 0.0

        return super().update(instance, validated_data)


