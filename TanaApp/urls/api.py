from django.urls import path
from TanaApp.views.owners.apis import OwnerListCreateView, OwnerRetrieveUpdateDestroyView, OwnerUpdateView, OwnerSearchView
from TanaApp.views.buildings.apis import BuildingListCreateView, BuildingRetrieveUpdateDestroyView, BuildingCustomerView, BuildingElevatorView, BuildingContractView, BuildingWarrantyView, BuildingSearchView
from TanaApp.views.elevators.apis import ElevatorListCreateView, ElevatorRetrieveUpdateDestroyView, ElevatorWarrantyListView, ElevatorCheckView, ElevatorSearchView, ElevatorInvoiceAPIView

from TanaApp.views.elevators.elevator_extras_discounts_api import (
    ElevatorExtraListCreateView,
    ElevatorExtraRetrieveUpdateDestroyView,
    ElevatorDiscountListCreateView,
    ElevatorDiscountRetrieveUpdateDestroyView,
)

from TanaApp.views.warranties.apis import WarrantyListCreateView, WarrantyExpiringView, BuildingWarrantyView, ActiveWarrantyView, ExpiredWarrantyView, AlmostExpiredView, VoidWarrantyView
from TanaApp.views.contracts.apis import ContractListCreateView, ContractRetrieveUpdateView, BuildingContractsView, ContractTotalView, ExpiredContractsView, ContractRegisterView, ContractCreateAttachAPIView, ContractPaymentStatusUpdateView, ContractCalculatorAPIView, ContractUpdateAPIView, ContractAuditTotalsView
from TanaApp.views.discounts.apis import ContractDiscountsView, DiscountRetrieveUpdateView, DiscountDeleteView
from TanaApp.views.employees.apis import EmployeeListCreateView, EmployeeRetrieveUpdateView, EmployeeRetrieveByEmailView
from TanaApp.views.expenses.apis import ExpenseListCreateView
from TanaApp.views.extras.apis import ContractExtrasView, ExtraRetrieveUpdateView, ExtraDeleteView


from TanaApp.views.partial_payments.apis import PartialPaymentCreateView, PartialPaymentRetrieveView, PartialPaymentUpdateView, PartialDeleteView, PartialDeleteByIdView
from TanaApp.views.timer.apis import TimerListCreateView, TimerRetrieveView, BuildingTimersView
from TanaApp.views.settings.settings_views import SettingsAPIView

urlpatterns = [
    # owners urls
    path('owners/', OwnerListCreateView.as_view(), name='owner-list-create'),
    path('owners/<int:id>/', OwnerRetrieveUpdateDestroyView.as_view(), name='owner-detail'),
    # path('owners/<int:id>/update/', OwnerUpdateView.as_view(), name='owner-update'),
    path('owners/search/', OwnerSearchView.as_view(), name='owner-search'),

    # buildings urls
    path('buildings/', BuildingListCreateView.as_view(), name='building-list'),
    path('buildings/<int:id>/', BuildingRetrieveUpdateDestroyView.as_view(), name='building-detail'),
    path('buildings/customer/<int:id>/', BuildingCustomerView.as_view(), name='building-customer'),
    path('buildings/elevators/', BuildingElevatorView.as_view(), name='building-elevators'),
    path('buildings/contracts/', BuildingContractView.as_view(), name='building-contracts'),
    path('buildings/warranties/', BuildingWarrantyView.as_view(), name='building-warranties'),
    path('buildings/search/', BuildingSearchView.as_view(), name='building-search'),

    # elevators urls
    path('elevators/', ElevatorListCreateView.as_view(), name='elevator-list'),
    path('elevators/<str:id>/', ElevatorRetrieveUpdateDestroyView.as_view(), name='elevator-detail'),
    path('elevators/<str:elevator_id>/invoice/', ElevatorInvoiceAPIView.as_view(), name='elevator-invoice'),
    path('elevators/building/<int:building_id>/', ElevatorWarrantyListView.as_view(), name='elevator-building'),

# elevator extras/discounts urls (scoped)

    path('elevators/<str:elevator_id>/extras/', ElevatorExtraListCreateView.as_view(), name='elevator-extras'),
    path('elevators/<str:elevator_id>/extras/<int:id>/', ElevatorExtraRetrieveUpdateDestroyView.as_view(), name='elevator-extra-detail'),

    path('elevators/<str:elevator_id>/discounts/', ElevatorDiscountListCreateView.as_view(), name='elevator-discounts'),
    path('elevators/<str:elevator_id>/discounts/<int:id>/', ElevatorDiscountRetrieveUpdateDestroyView.as_view(), name='elevator-discount-detail'),

    path('elevators/check/<int:building_id>/', ElevatorCheckView.as_view(), name='elevator-check'),
    path('elevators/search/', ElevatorSearchView.as_view(), name='elevator-search'),

    # warranties urls
    path('warranties/', WarrantyListCreateView.as_view(), name='warranty-list'),
    path('warranties/expiring/', WarrantyExpiringView.as_view(), name='expiring-warranties'),
    path('warranties/building/<int:building_id>/', BuildingWarrantyView.as_view(), name='building-warranties'),
    path('warranties/active/', ActiveWarrantyView.as_view(), name='active-warranties'),
    path('warranties/expired/', ExpiredWarrantyView.as_view(), name='expired-warranties'),
    path('warranties/almost-expired/', AlmostExpiredView.as_view(), name='almost-expired'),
    path('warranty/<int:warranty_id>/void/', VoidWarrantyView.as_view(), name='void-warranty'),

    # contracts urls
    path('contracts/', ContractListCreateView.as_view(), name='contract-list'),
    path('contracts/<int:id>/', ContractRetrieveUpdateView.as_view(), name='contract-detail'),
    path('contracts/building/<int:building_id>/', BuildingContractsView.as_view(), name='building-contracts'),
    path('contracts/<int:id>/total/', ContractTotalView.as_view(), name='contract-total'),
    path('contracts/expired/', ExpiredContractsView.as_view(), name='expired-contracts'),
    path('contract/register_forced/', ContractRegisterView.as_view(), name='contract-register'),
    path('contract/create-attach/', ContractCreateAttachAPIView.as_view(), name='contract-create-attach'),
    path('contracts/update-status/', ContractPaymentStatusUpdateView.as_view(), name="contract-update-payment-status"),
    path('contracts/<int:id>/calculator/', ContractCalculatorAPIView.as_view(), name='contract_calculator_api'),
    path('contracts/<int:contract_id>/update/', ContractUpdateAPIView.as_view(), name='contract-update'),
    path('contracts/audit-totals/', ContractAuditTotalsView.as_view(), name='contract-audit-totals'),

    # discounts urls
    path('discounts/contract/<int:contract_id>/', ContractDiscountsView.as_view(), name='contract-discounts'),
    path('discounts/<int:id>/', DiscountRetrieveUpdateView.as_view(), name='discount-detail'),
    path('discounts/<int:id>/delete/', DiscountDeleteView.as_view(), name='discount-delete'),

    # employees urls
    path('employees/', EmployeeListCreateView.as_view(), name='employee-list'),
    path('employees/<int:id>/', EmployeeRetrieveUpdateView.as_view(), name='employee-detail'),
    path('employees/by-email/', EmployeeRetrieveByEmailView.as_view(), name='employee-by-email'),

    # expenses urls
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list'),

    # extras urls
    path('extras/contract/<int:contract_id>/', ContractExtrasView.as_view(), name='contract-extras'),
    path('extras/<int:id>/', ExtraRetrieveUpdateView.as_view(), name='extra-detail'),
    path('extras/<int:id>/delete/', ExtraDeleteView.as_view(), name='extra-delete'),

    # partial payments urls
    path('partial-payments/', PartialPaymentCreateView.as_view(), name='partial-create'),
    path('partial-payments/<int:contract_id>/', PartialPaymentRetrieveView.as_view(), name='partial-detail'),
    path('partial-payments/<int:contract_id>/update/', PartialPaymentUpdateView.as_view(), name='partial-update'),
    path('partial-payments/<int:contract_id>/delete/', PartialDeleteView.as_view(), name='partial-delete'),
    path('partial-payments/<int:id>/delete-by-id/', PartialDeleteByIdView.as_view(), name='partial-delete-id'),

    # timers urls
    path('timers/', TimerListCreateView.as_view(), name='timer-list'),
    path('timers/<int:id>/', TimerRetrieveView.as_view(), name='timer-detail'),
    path('timers/building/<int:building_id>/', BuildingTimersView.as_view(), name='building-timers'),

    # settings urlls
    path('settings/', SettingsAPIView.as_view(), name='settings-api'),
]