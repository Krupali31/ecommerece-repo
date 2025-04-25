from django.contrib import admin

# Register your models here.
from .models import Products, Category, Customer, Order,  AboutUs

# Register your models here
admin.site.register(Products)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(AboutUs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'status', 'date']
    list_filter = ['status']