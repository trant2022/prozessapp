from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lieferung/<int:pk>/angekommen/', views.lieferung_angekommen, name='lieferung_angekommen'),
]
