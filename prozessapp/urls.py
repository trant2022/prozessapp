from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # UI views (order list & detail)
    path('', include('process.urls')),  # / → order_list; /orders/<pk>/ → order_detail
]
