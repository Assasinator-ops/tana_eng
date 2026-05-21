from django.utils import timezone
from django.views.generic import TemplateView
from TanaApp.models import DbWarranty, DbContract
from datetime import timedelta

class NotificationListView(TemplateView):
    template_name = "pages/webs/notifications/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        in_7_days = today + timedelta(days=7)

        # Contracts
        expired_contracts = DbContract.objects.filter(end_date__lt=today)
        expiring_contracts = DbContract.objects.filter(end_date__range=(today, in_7_days))

        # Get active contract building and elevator IDs
        active_contract_building_ids = DbContract.objects.filter(
            end_date__gte=today
        ).values_list("building_id", flat=True)

        active_contract_elevator_ids = DbContract.objects.filter(
            end_date__gte=today
        ).values_list("elevators__id", flat=True)

        # Warranties not under contract
        expired_warranties = DbWarranty.objects.filter(
            end_date__lt=today
        ).exclude(
            elevator__building_id__in=active_contract_building_ids
        ).exclude(
            elevator_id__in=active_contract_elevator_ids
        )

        expiring_warranties = DbWarranty.objects.filter(
            end_date__range=(today, in_7_days)
        ).exclude(
            elevator__building_id__in=active_contract_building_ids
        ).exclude(
            elevator_id__in=active_contract_elevator_ids
        )

        grouped_notifications = [
            ("Expired Warranties", expired_warranties),
            ("Expiring Soon Warranties", expiring_warranties),
            ("Expired Contracts", expired_contracts),
            ("Expiring Soon Contracts", expiring_contracts),
        ]

        context.update({
            "grouped_notifications": grouped_notifications,
            "total_notifications": sum(len(qs) for _, qs in grouped_notifications),
        })
        return context