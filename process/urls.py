from django.urls import path
from . import views

urlpatterns = [
    # Dashboard / Auflistung aller Lieferungen
    path('', views.lieferung_list, name='lieferung_list'),

    # Neue Lieferung erstellen
    path('lieferung/erstellen/', views.create_lieferung, name='create_lieferung'),

    # Lieferung als angekommen markieren
    path('lieferung/<int:pk>/angekommen/', views.lieferung_angekommen, name='lieferung_angekommen'),

    # Lieferung bearbeiten
    path('lieferung/<int:pk>/bearbeiten/', views.lieferung_edit, name='lieferung_edit'),

    # Detail-Ansicht einer Lieferung
    path('lieferung/<int:pk>/', views.lieferung_detail, name='lieferung_detail'),

    # Excel-Upload für Positionen
    path('upload_positions/', views.upload_positions, name='upload_positions'),
]
