from django.urls import path
from . import views

urlpatterns = [
    '''
    # Owner URLs
    path('owners/', views.ListOwnersView.as_view(), name='list-owners'),
    path('owners/create/', views.CreateOwnerView.as_view(), name='create-owner'),
    path('owners/<int:id>/', views.RetrieveOwnerView.as_view(), name='retrieve-owner'),
    path('owners/update/<int:id>/', views.UpdateOwnerView.as_view(), name='update-owner'),
    path('owners/delete/<int:id>/', views.DeleteOwnerView.as_view(), name='delete-owner'),
    path('owners/search/', views.SearchOwnerView.as_view(), name='search-owner'),

    # Building URLs
    path('create/', views.CreateBuildingView.as_view(), name='create-building'),
    path('get/<str:name>/', views.GetBuildingView.as_view(), name='get-building'),
    path('customer/<int:id>/', views.GetCustomerBuildingsView.as_view(), name='get-customer-buildings'),
    path('all/', views.GetAllBuildingsView.as_view(), name='get-all-buildings'),
    path('one/<int:id>/', views.GetSingleBuildingView.as_view(), name='get-one-building'),
    path('update/<int:id>/', views.UpdateBuildingView.as_view(), name='update-building'),
    path('elevators/', views.GetBuildingElevatorsView.as_view(), name='get-building-elevators'),
    path('contracts/', views.GetBuildingContractsView.as_view(), name='get-building-contracts'),
    path('warranty/', views.GetBuildingsOnWarrantyView.as_view(), name='get-buildings-on-warranty'),
    path('search/', views.SearchBuildingView.as_view(), name='search-building'),

    # Elevator URLs
    path('elevators/', views.ElevatorListView.as_view(), name='elevator-list'),
    path('elevators/create/', views.ElevatorCreateView.as_view(), name='elevator-create'),
    path('elevators/<int:id>/', views.ElevatorDetailView.as_view(), name='elevator-detail'),
    path('elevators/check/<int:id>/', views.ElevatorCheckView.as_view(), name='elevator-check'),
    path('elevators/search/', views.ElevatorSearchView.as_view(), name='elevator-search'),

    # Contract URLs
    path('contracts/', views.ContractListView.as_view(), name='contract-list'),
    path('contracts/create/', views.ContractCreateView.as_view(), name='contract-create'),
    path('contracts/<int:id>/', views.ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:id>/update/', views.ContractUpdateView.as_view(), name='contract-update'),
    path('contracts/<int:id>/delete/', views.ContractDeleteView.as_view(), name='contract-delete'),
    path('contracts/expired/', views.ExpiredContractsView.as_view(), name='expired-contracts'),

    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<str:email>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/update/<int:id>/', views.EmployeeUpdateView.as_view(), name='employee-update'),

    # Extra Payment URLs
    path('extra/', views.ExtraPaymentListCreateView.as_view(), name='extra-list-create'),
    path('extra/<int:pk>/', views.ExtraPaymentRetrieveUpdateView.as_view(), name='extra-detail-update'),

    # Partial Payment URLs
    path("partial/", views.PartialPaymentListCreateView.as_view(), name="partial-list-create"),
    path("partial/<int:id>/", views.PartialPaymentRetrieveUpdateView.as_view(), name="partial-retrieve-update"),

    # Warranty URLs
    path('warranties/', views.WarrantyListCreateView.as_view(), name='warranty-list-create'),
    path('warranties/<int:pk>/', views.WarrantyRetrieveView.as_view(), name='warranty-detail'),
    path('warranties/expiring/', views.ExpiringWarrantyListView.as_view(), name='warranty-expiring'),
    path('warranties/active/', views.ActiveWarrantyListView.as_view(), name='warranty-active'),
    path('warranties/expired/', views.ExpiredWarrantyListView.as_view(), name='warranty-expired'),
    path('warranties/almost-expired/', views.WarrantyAlmostExpiredListView.as_view(), name='warranty-almost-expired'),

    # Discount URLs
    path('discounts/<int:contract_id>/', views.DiscountListCreateView.as_view(), name='discount-list-create'),
    path('discount/<int:pk>/', views.DiscountRetrieveUpdateView.as_view(), name='discount-retrieve-update'),
    '''
]
