from django.contrib import admin
from .models import Supplier, Customer, DeviceType, DeviceModel, Order, OrderPosition

admin.site.register([Supplier, Customer, DeviceType, DeviceModel, Order, OrderPosition])
