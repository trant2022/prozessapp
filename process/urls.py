from django.urls import path
from . import views

urlpatterns = [
    # Dashboard / Liste aller Lieferungen
    path('', views.lieferung_list, name='order_list'),

    # Neue Lieferung anlegen
    path('lieferung/erstellen/', views.create_lieferung, name='create_lieferung'),

    # Excel-Upload für Auftragspositionen
    path('upload_positions/', views.upload_positions, name='upload_positions'),

    # Detailansicht einer einzelnen Lieferung
    path('lieferung/<int:pk>/', views.lieferung_detail, name='lieferung_detail'),

    # Lieferung als «angekommen» markieren
    path('lieferung/<int:pk>/angekommen/', views.lieferung_angekommen, name='lieferung_angekommen'),

    # Lieferung nachträglich bearbeiten (z.B. Kommentar, Datum, Menge)
    path('lieferung/<int:pk>/bearbeiten/', views.lieferung_edit, name='lieferung_edit'),
]
