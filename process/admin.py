from django.contrib import admin
from .models import Lieferant, Lieferung, Gerätetyp, Gerätemodell, Auftragsposition

@admin.register(Lieferant)
class LieferantAdmin(admin.ModelAdmin):
    list_display = ('nummer', 'name')

@admin.register(Lieferung)
class LieferungAdmin(admin.ModelAdmin):
    list_display = ('liefernummer','lieferant','bestelldatum','erwartetes_datum','effektives_datum','gesamtmenge','kommentar')
    list_editable = ('kommentar',)

@admin.register(Gerätetyp)
class GerätetypAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Gerätemodell)
class GerätemodellAdmin(admin.ModelAdmin):
    list_display = ('typ','name')

@admin.register(Auftragsposition)
class AuftragspositionAdmin(admin.ModelAdmin):
    list_display = ('auftrag','positionsnummer','geraetetyp','geraetemodell','menge')
