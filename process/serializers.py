from rest_framework import serializers
from .models import Supplier, Customer, DeviceType, DeviceModel, Order, OrderPosition

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = '__all__'

class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceModel
        fields = '__all__'

class OrderPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPosition
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    positions = OrderPositionSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
