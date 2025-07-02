# prozessapp/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from process import views as process_views

router = routers.DefaultRouter()
router.register(r'suppliers', process_views.SupplierViewSet)
router.register(r'customers', process_views.CustomerViewSet)
router.register(r'devicetypes', process_views.DeviceTypeViewSet)
router.register(r'devicemodels', process_views.DeviceModelViewSet)
router.register(r'orders', process_views.OrderViewSet)
router.register(r'orderpositions', process_views.OrderPositionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('process.urls')),   # Root-URLs in process/urls.py
    path('api/', include('rest_framework.urls')),  # DRF Login falls nötig
]