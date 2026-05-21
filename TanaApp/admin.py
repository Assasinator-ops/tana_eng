from django.contrib import admin
from django.urls import path
from django.urls import reverse
from TanaApp.views.contracts.contracts_views import ContractCalculatorView
from .models import (
    UserType, DbUser, DbOwner, DbBuilding, ElevatorStatus, DbElevator,
    DbBuildingManager, DiscountType, DbDiscount, DbExtra, DbMessage, DbWarranty,
    ContratE, DbContract, DbBuildingStatus, DBPartialPyment,
    DbTotal, DbExpense, GlobalSettings, PersonalizedSettings
)

@admin.register(DbUser)
class DbUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'usertype', 'phone', 'status')
    search_fields = ('name', 'email', 'phone')

@admin.register(DbOwner)
class DbOwnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone1', 'phone2')
    search_fields = ('name', 'email', 'phone1')

@admin.register(DbBuilding)
class DbBuildingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'phone1', 'email1', 'owner')
    search_fields = ('name', 'address', 'phone1', 'email1')

@admin.register(DbElevator)
class DbElevatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'commissionnumber', 'name', 'model', 'building', 'registerd_date')
    search_fields = ('id', 'commissionnumber', 'name', 'model')

@admin.register(DbBuildingManager)
class DbBuildingManagerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone1', 'building')
    search_fields = ('name', 'email', 'phone1')

@admin.register(DbDiscount)
class DbDiscountAdmin(admin.ModelAdmin):
    list_display = ('id', 'time', 'discount_type', 'discount_money', 'contract')
    search_fields = ('discount_type',)

@admin.register(DbExtra)
class DbExtraAdmin(admin.ModelAdmin):
    list_display = ('id', 'money', 'contract')
    search_fields = ('discription', 'discription1')

@admin.register(DbMessage)
class DbMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'employee')
    search_fields = ('title',)

@admin.register(DbWarranty)
class DbWarrantyAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'elevator')

@admin.register(DbContract)
class DbContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'building', 'start_date', 'end_date', 'paytime', 'payed')
    search_fields = ('building__name',)
'''
@admin.register(DBContractElevator)
class DBContractElevatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'elevator')
'''
@admin.register(DbBuildingStatus)
class DbBuildingStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'building_status', 'building')

@admin.register(DBPartialPyment)
class DBPartialPymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'total', 'contract')

@admin.register(DbTotal)
class DbTotalAdmin(admin.ModelAdmin):
    list_display = ('id', 'total', 'is_Actiave', 'contract')

@admin.register(DbExpense)
class DbExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'capacity', 'number_of_stops', 'item')

@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'default_currency', 'notifications_enabled')
    fieldsets = (
        ('Core', {'fields': ('company_name', 'default_currency', 'notifications_enabled')}),
        ('Appearance', {'fields': ('theme_color', 'date_format')}),
        ('Security', {'fields': ('require_2fa', 'password_expiry_days', 'login_attempts_limit')}),
    )

@admin.register(PersonalizedSettings)
class PersonalizedSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'notifications_enabled', 'messages_enabled')
    list_select_related = ('user',)
    search_fields = ('user__username',)
