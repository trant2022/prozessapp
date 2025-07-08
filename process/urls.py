from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('lieferung/erstellen/', views.create_lieferung, name='create_lieferung'),
    path('lieferung/<int:pk>/angekommen/', views.lieferung_angekommen, name='lieferung_angekommen'),
    path('lieferung/<int:pk>/bearbeiten/', views.lieferung_edit, name='lieferung_edit'),
    path('positionen/upload/', views.upload_positions, name='upload_positions'),
    path('lieferung/<int:pk>/positionen/', views.positionen_liste, name='lieferung_positionen'),
]
