from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
]