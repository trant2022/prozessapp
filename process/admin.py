from django.contrib import admin
from .models import (
    Lieferant,
    Lieferung,
    Gerätetyp,
    Gerätemodell,
    Lieferungsposition,
)

admin.site.register([
    Lieferant,
    Lieferung,
    Gerätetyp,
    Gerätemodell,
    Lieferungsposition,
])
