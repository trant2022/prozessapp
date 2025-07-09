from django.urls import path
from . import views

urlpatterns = [
    path('', views.lieferung_list, name='lieferung_list'),
    path('lieferung/erstellen/', views.create_lieferung, name='create_lieferung'),
    path('lieferung/<int:pk>/angekommen/', views.lieferung_angekommen, name='lieferung_angekommen'),
    path('lieferung/<int:pk>/loeschen/', views.lieferung_loeschen, name='lieferung_loeschen'),
    path('lieferung/<int:pk>/bearbeiten/', views.lieferung_edit, name='lieferung_edit'),
    path('lieferung/<int:pk>/', views.lieferung_detail, name='lieferung_detail'),
    path('upload_positions/', views.upload_positions, name='upload_positions'),
]
