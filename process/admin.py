from django.contrib import admin
from .models import Lieferant, Lieferung

@admin.register(Lieferant)
class LieferantAdmin(admin.ModelAdmin):
    list_display = ("nummer", "name")


@admin.register(Lieferung)
class LieferungAdmin(admin.ModelAdmin):
    list_display = (
        "liefernummer",
        "lieferant",
        "bestelldatum",
        "erwartetes_datum",
        "gesamtmenge",
        "effektives_datum",
    )
