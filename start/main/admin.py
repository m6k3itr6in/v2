from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.admin.sites import NotRegistered
from .models import CoffeeShop, Worker, Shift, UserProfile, ShopAdmin

# Register your models here.
try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

@admin.register(CoffeeShop)
class CoffeeShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'short_code', 'minimum_workers']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'experience_years', 'start_date_experience_years', 'hourly_rate', 'coffee_shop']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']

@admin.register(ShopAdmin)
class ShopAdminAdmin(admin.ModelAdmin):
    list_display = ['user', 'coffee_shop', 'assigned_at']