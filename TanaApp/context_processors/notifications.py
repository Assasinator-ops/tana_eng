# context_processors.py
from TanaApp.models import DbWarranty, DbContract
from django.utils import timezone
from datetime import timedelta

def notification_count(request):
    today = timezone.now()
    in_7_days = today + timedelta(days=7)

    # Contracts that are still active
    active_contracts = DbContract.objects.filter(end_date__gte=today)

    # Get covered buildings and elevators
    active_contract_building_ids = active_contracts.values_list("building_id", flat=True)
    active_contract_elevator_ids = active_contracts.values_list("elevators__id", flat=True)  # for ManyToManyField

    # Filter warranties NOT under contract
    expired_warranties = DbWarranty.objects.filter(end_date__lt=today) \
        .exclude(elevator__building_id__in=active_contract_building_ids) \
        .exclude(elevator_id__in=active_contract_elevator_ids)

    expiring_warranties = DbWarranty.objects.filter(end_date__range=(today, in_7_days)) \
        .exclude(elevator__building_id__in=active_contract_building_ids) \
        .exclude(elevator_id__in=active_contract_elevator_ids)

    expired_contracts = DbContract.objects.filter(end_date__lt=today)
    expiring_contracts = DbContract.objects.filter(end_date__range=(today, in_7_days))

    all_notifications = list(expired_warranties) + list(expiring_warranties) + list(expired_contracts) + list(expiring_contracts)

    return {
        "total_notifications": len(all_notifications),
        "notifications": all_notifications,
    }