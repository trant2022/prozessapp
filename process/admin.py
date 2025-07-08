from django.contrib import admin
from .models import (
    Lieferant,
    Kunde,
    Gerätetyp,
    Gerätemodell,
    Auftrag,
    Auftragsposition,
    Lieferung,
)

@admin.register(Lieferant)
class LieferantAdmin(admin.ModelAdmin):
    list_display = ('nummer', 'name')
    search_fields = ('nummer', 'name')


@admin.register(Kunde)
class KundeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Gerätetyp)
class GerätetypAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Gerätemodell)
class GerätemodellAdmin(admin.ModelAdmin):
    list_display = ('typ', 'name')
    list_filter  = ('typ',)
    search_fields = ('name',)


@admin.register(Auftrag)
class AuftragAdmin(admin.ModelAdmin):
    # nur diese Felder im Formular sichtbar
    fields = (
        'auftragsnummer',
        'lieferant',
        'bestelldatum',
        'lieferdatum',
        'gesamtmenge',   # jetzt manuell eingeben
    )
    readonly_fields = ()  # gesamtmenge ist jetzt editierbar
    list_display = (
        'auftragsnummer',
        'lieferant',
        'bestelldatum',
        'lieferdatum',
        'gesamtmenge',
    )
    list_filter  = ('lieferant',)
    search_fields = ('auftragsnummer',)


@admin.register(Auftragsposition)
class AuftragspositionAdmin(admin.ModelAdmin):
    list_display = (
        'auftrag',
        'positionsnummer',
        'geraetetyp',
        'geraetemodell',
        'menge',
    )
    list_filter  = ('auftrag', 'geraetetyp')
    search_fields = ('auftrag__auftragsnummer',)


@admin.register(Lieferung)
class LieferungAdmin(admin.ModelAdmin):
    # nur die vier minimalen Felder
    fields = (
        'lieferant',
        'bestelldatum',
        'erwartetes_datum',
        'gesamtmenge',
    )
    readonly_fields = ()  # gesamtmenge kommt manuell
    list_display = (
        'liefernummer',
        'lieferant',
        'bestelldatum',
        'erwartetes_datum',
        'gesamtmenge',
    )
    list_filter  = ('lieferant',)
    search_fields = ('liefernummer',)
