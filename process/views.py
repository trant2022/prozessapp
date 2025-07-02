from rest_framework import viewsets
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404

from .models import Supplier, Customer, DeviceType, DeviceModel, Order, OrderPosition
from .serializers import (
    SupplierSerializer, CustomerSerializer,
    DeviceTypeSerializer, DeviceModelSerializer,
    OrderSerializer, OrderPositionSerializer
)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer

class DeviceModelViewSet(viewsets.ModelViewSet):
    queryset = DeviceModel.objects.all()
    serializer_class = DeviceModelSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class OrderPositionViewSet(viewsets.ModelViewSet):
    queryset = OrderPosition.objects.all()
    serializer_class = OrderPositionSerializer

def order_list(request):
    orders = (
        Order.objects
        .select_related('supplier', 'customer')
        .order_by('-order_date')
    )
    return render(request, 'process/order_list.html', {'orders': orders})

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Lädt alle Positionen und ggf. verwandte Objekte
    positions = order.positions.select_related('device_type', 'device_model').all()
    return render(request, 'process/order_detail.html', {
        'order': order,
        'positions': positions,
    })