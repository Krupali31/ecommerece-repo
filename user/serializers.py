from rest_framework import serializers
from .models import Order, ContactMessage

class OrderDataSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    price = serializers.IntegerField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    date = serializers.DateField(required=True)
    status = serializers.CharField(required=True)
    payment_status = serializers.CharField(required=True)
    payment_method = serializers.CharField(required=True)
    payment_reference = serializers.CharField(required=True)

class OrderSerializer(serializers.ModelSerializer):
    data = OrderDataSerializer()

    class Meta:
        model = Order
        fields = "__all__"

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at']