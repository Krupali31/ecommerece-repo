from django.contrib import admin

# Register your models here.
from .models import Products, Category, Customer, Order,  AboutUs, ContactMessage

# Register your models here

admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(AboutUs)
admin.site.register(ContactMessage)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'image']
    search_fields = ['name']

admin.site.register(Products, ProductAdmin)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'customer','data', 'created_at', 'updated_at']
    search_fields = ['customer__username', 'product__name']
    list_filter = ['created_at']