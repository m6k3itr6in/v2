from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.admin.sites import NotRegistered
from .models import CoffeeShop, Worker, Shift, UserProfile, ShopAdmin, ShiftRequest

# Register your models here.
try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

@admin.register(CoffeeShop)
class CoffeeShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'short_code', 'minimum_workers', 'hourly_rate']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'experience_years', 'start_date_experience_years', 'coffee_shop']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']

@admin.register(ShopAdmin)
class ShopAdminAdmin(admin.ModelAdmin):
    list_display = ['user', 'coffee_shop', 'assigned_at']

@admin.register(ShiftRequest)
class ShiftRequestAdmin(admin.ModelAdmin):
    list_display = ['shift', 'worker', 'reason', 'status', 'requested_at', 'approved_by', 'approved_at', 'taken_by', 'taken_at']