from rest_framework import serializers
from TanaApp.models import DbExtra
from decimal import Decimal, ROUND_HALF_UP

from TanaApp.contract_payment import compute_contract_totals





class ExtraSerializer(serializers.ModelSerializer):
    money = serializers.FloatField(required=False, default=0.0)

    class Meta:
        model = DbExtra
        fields = '__all__'
        extra_kwargs = {
            'discription': {'required': False},  # Note preserved typo
            'discription1': {'required': False},
            'money': {'required': False},
        }

    def validate(self, attrs):
        attrs.setdefault('money', 0.0)
        return attrs


class ExtraManageSerializer(serializers.ModelSerializer):
    """Manage-page serializer for DbExtra.

    Behavior:
    - If client sends percentage but not money, compute `money` from percentage.
    - If client sends money (legacy), keep it.

    Rounding:
    - money is rounded to 2 decimals using Decimal quantize.
    """

    class Meta:
        model = DbExtra
        fields = ['percentage', 'money', 'discription', 'discription1']
        extra_kwargs = {
            'discription': {'required': False},
            'discription1': {'required': False},
            'money': {'required': False},
            'percentage': {'required': False},
        }

    def validate(self, attrs):
        """Normalize null/blank and guarantee deterministic values.

        UI can send null for both percentage and money. In that case we default to
        percentage=0 and money=0 so calculator totals never break.
        """

        def _blank_to_none(v):
            if v in ('',):
                return None
            return v

        if 'money' in attrs:
            attrs['money'] = _blank_to_none(attrs['money'])
            if attrs['money'] is None:
                # keep None for now; create/update will resolve based on pct
                pass
        if 'percentage' in attrs:
            attrs['percentage'] = _blank_to_none(attrs['percentage'])

        money = attrs.get('money', None)
        pct = attrs.get('percentage', None)

        money_missing = money is None
        pct_missing = pct is None

        # If only one side is present => compute the other.
        if pct_missing and not money_missing:
            # money provided, percentage missing => compute percentage from base net
            # (we do it later in create/update where we have contract).
            return attrs

        if not pct_missing and money_missing:
            # pct provided, money missing => compute in create/update.
            return attrs

        # Both missing => deterministic default.
        if pct_missing and money_missing:
            attrs['percentage'] = 0.0
            attrs['money'] = 0.0

        return attrs


    def _quantize_2(self, raw: float) -> float:
        return float(Decimal(str(raw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _compute_money_delta(self, *, contract, pct: float) -> float:
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
        money = validated_data.get('money', None)

        # Normalize '' => None (just in case)
        if pct in ('',):
            pct = None
        if money in ('',):
            money = None

        # Compute missing side(s)
        if money is None and pct is not None:
            validated_data['money'] = self._compute_money_delta(contract=contract, pct=float(pct))
        elif pct is None and money is not None:
            totals_before = compute_contract_totals(contract)
            net_before = float(totals_before['net_total'])
            if net_before == 0:
                validated_data['percentage'] = 0.0
            else:
                validated_data['percentage'] = float(money) / net_before * 100.0
        elif pct is None and money is None:
            # Both missing: should have been defaulted in validate(), but be defensive.
            validated_data['percentage'] = 0.0
            validated_data['money'] = 0.0

        return super().create({**validated_data, 'contract_id': contract_id})


    def update(self, instance, validated_data):
        contract = instance.contract

        pct = validated_data.get('percentage', getattr(instance, 'percentage', None))
        money = validated_data.get('money', None)

        if pct in ('',):
            pct = None
        if money in ('',):
            money = None

        # Compute missing side(s) based on provided values.
        if money is None and pct is not None:
            validated_data['money'] = self._compute_money_delta(contract=contract, pct=float(pct))
        elif pct is None and money is not None:
            totals_before = compute_contract_totals(contract)
            net_before = float(totals_before['net_total'])
            if net_before == 0:
                validated_data['percentage'] = 0.0
            else:
                validated_data['percentage'] = float(money) / net_before * 100.0
        elif pct is None and money is None:
            validated_data['percentage'] = 0.0
            validated_data['money'] = 0.0

        return super().update(instance, validated_data)


