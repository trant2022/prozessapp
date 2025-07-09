from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
import pandas as pd

from .models import (
    Lieferung,
    Lieferant,
    Gerätetyp,
    Gerätemodell,
    Lieferungsposition,
)

def lieferung_list(request):
    lieferungen  = Lieferung.objects.all().order_by('liefernummer')
    lieferanten  = Lieferant.objects.all().order_by('name')
    today        = timezone.localdate()

    # KPI
    devices_on_the_way = (
        Lieferung.objects
                 .filter(effektives_datum__isnull=True)
                 .aggregate(total=Sum('gesamtmenge'))['total'] or 0
    )
    devices_arrived = (
        Lieferung.objects
                 .filter(effektives_datum__isnull=False)
                 .aggregate(total=Sum('gesamtmenge'))['total'] or 0
    )
    processed_internal = devices_arrived
    processed_external = 0

    context = {
        "lieferungen": lieferungen,
        "lieferanten": lieferanten,
        "today": today,
        "kpi": {
            "devices_on_the_way": devices_on_the_way,
            "devices_arrived": devices_arrived,
            "processed_internal": processed_internal,
            "processed_external": processed_external,
        },
    }
    return render(request, "process/order_list.html", context)


def lieferung_detail(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    # hol alle importierten Positionen
    positionen = lieferung.positionen.all()
    return render(request, 'process/lieferung_detail.html', {
        'lieferung': lieferung,
        'positionen': positionen,
    })


def create_lieferung(request):
    if request.method == "POST":
        name      = request.POST.get('lieferant_name')
        supplier, _ = Lieferant.objects.get_or_create(
            name=name,
            defaults={'nummer': str(
                int(Lieferant.objects.order_by('-nummer').first().nummer or "0") + 1
            )}
        )
        bestelldatum      = request.POST.get('bestelldatum') or timezone.localdate()
        erwartetes        = request.POST.get('erwartetes_datum') or None
        menge             = int(request.POST.get('gesamtmenge') or 0)
        kommentar         = request.POST.get('kommentar', '')

        Lieferung.objects.create(
            lieferant=supplier,
            bestelldatum=bestelldatum,
            erwartetes_datum=erwartetes,
            gesamtmenge=menge,
            kommentar=kommentar
        )
    return redirect("lieferung_list")


def lieferung_angekommen(request, pk):
    if request.method == "POST":
        lieferung = get_object_or_404(Lieferung, pk=pk)
        lieferung.effektives_datum = timezone.localdate()
        lieferung.save()
    return redirect("lieferung_list")


def lieferung_edit(request, pk):
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)
    if request.method == 'POST':
        lieferung.bestelldatum        = request.POST.get('bestelldatum', lieferung.bestelldatum)
        ed = request.POST.get('erwartetes_datum')
        lieferung.erwartetes_datum    = ed if ed else None
        lieferung.gesamtmenge         = int(request.POST.get('gesamtmenge', lieferung.gesamtmenge))
        lieferung.kommentar           = request.POST.get('kommentar', lieferung.kommentar)
        lieferung.save()
        return redirect('lieferung_list')

    return render(request, 'process/lieferung_edit.html', {
        'lieferung': lieferung,
        'lieferanten': Lieferant.objects.all().order_by('name'),
    })


@require_POST
def upload_positions(request):
    positions_file = request.FILES.get('positions_file')
    if not positions_file:
        return HttpResponseBadRequest("Keine Datei ausgewählt")

    # DataFrame einlesen
    df = pd.read_excel(positions_file)
    print("Excel-Spalten:", df.columns.tolist())  # Hilft beim Debugging

    for _, row in df.iterrows():
        # Exakte Header-Namen aus deinem Excel
        nr          = row.get('Auftragsnummer')
        typ_name    = row.get('Gerätetyp')
        modell_name = row.get('Modell')

        if nr is None:
            continue

        try:
            lieferung = Lieferung.objects.get(liefernummer=int(nr))
        except Lieferung.DoesNotExist:
            print(f"Lieferung {nr} nicht gefunden, übersprungen")
            continue

        if not typ_name or not modell_name:
            print(f"Typ/Modell fehlt in Zeile für Lieferung {nr}, übersprungen")
            continue

        typ, _    = Gerätetyp.objects.get_or_create(name=typ_name)
        modell, _ = Gerätemodell.objects.get_or_create(typ=typ, name=modell_name)

        Lieferungsposition.objects.update_or_create(
            lieferung=lieferung,
            positionsnummer=int(row.get('Positionsnummer') or 0),
            defaults={
                'geraetetyp': typ,
                'geraetemodell': modell,
                'farbe': row.get('Farbe', ''),
                'speicher': row.get('Speicher', ''),
                'ram': row.get('RAM', ''),
                'prozessor': row.get('Prozessor', ''),
                'zustand': row.get('Zustand', ''),
                'menge': int(row.get('Menge') or 0),
            }
        )

    return redirect('order_list')