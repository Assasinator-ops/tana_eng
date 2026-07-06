# urls.py
from django.urls import path
from TanaApp.views.system.dashboard.dash_views import IndexView, DashboardView, OwnerListView, OwnerDetailView, OwnerCreateView, AddBuildingForOwnerAPIView
from TanaApp.views.buildings.buildings_views import BuildingDashboardView, BuildingAddView, BuildingDetailView, AddElevatorForBuildingAPIView
from TanaApp.views.elevators.elevators_views import ElevatorDashboardView, ElevatorAddView, ElevatorDetailView, AddElevatorToContractView
from TanaApp.views.contracts.contracts_views import contract_dashboard, ContractCalculatorView, ContractManageView
from TanaApp.views.contracts.contract_delete_views import ContractSoftDeleteView, ContractScarDeleteView
from TanaApp.views.notifications.notifications_views import NotificationListView
from TanaApp.views.settings.settings_views import SettingsView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('owners/dashboard/', OwnerListView.as_view(), name='owner-list'),
    path('owners/<int:pk>/detail/', OwnerDetailView.as_view(), name='owner-detail-page'),
    path('owners/<int:pk>/add-building/', AddBuildingForOwnerAPIView.as_view(), name='add-building-for-owner'),
    path('owners/create/', OwnerCreateView.as_view(), name='owner-create'),

    path('buildings/dashboard/', BuildingDashboardView.as_view(), name='buildings-dashboard'),
    path('buildings/add/', BuildingAddView.as_view(), name='building-add'),
    path('buildings/<int:id>/detail/', BuildingDetailView.as_view(), name='buildings-detail-page'),
    path('buildings/<int:pk>/add-elevator/', AddElevatorForBuildingAPIView.as_view(), name='add-elevator-for-building'),

    path('elevators/dashboard/', ElevatorDashboardView.as_view(), name='elevator-dashboard'),
    path('elevators/add/', ElevatorAddView.as_view(), name='elevator-add'),
    path('elevators/<str:id>/detail/', ElevatorDetailView.as_view(), name='elevator-detail-page'),
    # path('contracts/<int:contract_id>/add-elevators/', AddElevatorToContractView.as_view(), name='add-elevator-to-contract'),

    path('contracts/dashboard/<int:building_id>/', contract_dashboard, name='contract-dashboard'),
    path('contracts/<int:id>/calculator/', ContractCalculatorView.as_view(), name='contract_calculator'),
    path('contracts/<int:id>/manage/', ContractManageView.as_view(), name='contract-manage'),

    path('contracts/<int:id>/delete/', ContractSoftDeleteView.as_view(), name='contract-soft-delete'),
    path('contracts/scars/<int:scar_id>/delete/', ContractScarDeleteView.as_view(), name='contract-scar-delete'),


    path('notifications/', NotificationListView.as_view(), name='notifications-list'),

    path('settings/', SettingsView.as_view(), name='settings-page'),
]