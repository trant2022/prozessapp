import pandas as pd

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    Lieferant,
    Lieferung,
    Gerätetyp,
    Gerätemodell,
    Lieferungsposition,
)


def generate_number():
    last = Lieferant.objects.order_by('-nummer').first()
    if last and last.nummer.isdigit():
        return str(int(last.nummer) + 1)
    return '1'


def lieferung_list(request):
    lieferungen = Lieferung.objects.all()
    lieferanten = Lieferant.objects.all()

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
        'lieferungen': lieferungen,
        'lieferanten': lieferanten,
        'kpi': {
            'devices_on_the_way': devices_on_the_way,
            'devices_arrived': devices_arrived,
            'processed_internal': processed_internal,
            'processed_external': processed_external,
        },
        'today': timezone.localdate(),  # für das Default-Datum im Modal
    }
    return render(request, "process/order_list.html", context)


@require_POST
def create_lieferung(request):
    supplier_name    = request.POST.get('lieferant_name')
    bestelldatum     = request.POST.get('bestelldatum')
    erwartetes_datum = request.POST.get('erwartetes_datum') or None
    gesamtmenge      = request.POST.get('gesamtmenge')
    kommentar        = request.POST.get('kommentar', '')

    if supplier_name and bestelldatum and gesamtmenge:
        # Lieferant nach Name holen (Name kommt aus <datalist>)
        lieferant = get_object_or_404(Lieferant, name=supplier_name)
        Lieferung.objects.create(
            lieferant=lieferant,
            bestelldatum=bestelldatum,
            erwartetes_datum=erwartetes_datum,
            gesamtmenge=int(gesamtmenge),
            kommentar=kommentar,
        )
    return redirect('lieferung_list')


@require_POST
def lieferung_angekommen(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    lieferung.mark_arrived()
    return redirect('lieferung_detail', pk=pk)


def lieferung_detail(request, pk):
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)
    return render(request, "process/lieferung_detail.html", {
        'lieferung': lieferung
    })


def lieferung_edit(request, pk):
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)

    if request.method == 'POST':
        lieferung.bestelldatum      = request.POST.get('bestelldatum', lieferung.bestelldatum)
        ed = request.POST.get('erwartetes_datum')
        lieferung.erwartetes_datum  = ed if ed else None
        lieferung.gesamtmenge       = int(request.POST.get('gesamtmenge', lieferung.gesamtmenge))
        lieferung.kommentar         = request.POST.get('kommentar', lieferung.kommentar)
        lieferung.save()
        return redirect('lieferung_list')

    return render(request, "process/lieferung_edit.html", {
        'lieferung': lieferung,
        'lieferanten': Lieferant.objects.all(),
    })


@require_POST
def upload_positions(request):
    positions_file = request.FILES.get('positions_file')
    if not positions_file:
        return HttpResponseBadRequest("Keine Datei ausgewählt")

    # Excel einlesen
    try:
        df = pd.read_excel(positions_file)
    except Exception as e:
        return HttpResponseBadRequest(f"Dateilesefehler: {e}")

    # Über alle Zeilen iterieren und Positionen anlegen
    for _, row in df.iterrows():
        nr = row.get('Liefernummer')
        if pd.isna(nr):
            continue
        try:
            lieferung = Lieferung.objects.get(liefernummer=int(nr))
        except (Lieferung.DoesNotExist, ValueError):
            continue

        # Gerätetyp bestimmen
        typ_name = row.get('Geräteart') or row.get('Gerätetyp') or row.get('Geraetetyp')
        if not typ_name or pd.isna(typ_name):
            continue
        typ, _ = Gerätetyp.objects.get_or_create(name=str(typ_name).strip())

        # Modell bestimmen
        modell_name = row.get('Gerätemodell') or row.get('Modell')
        if not modell_name or pd.isna(modell_name):
            continue
        modell, _ = Gerätemodell.objects.get_or_create(
            typ=typ,
            name=str(modell_name).strip()
        )

        # Menge
        menge = row.get('Menge')
        menge = int(menge) if not pd.isna(menge) else 0

        # Position anlegen (positionsnummer wird automatisch vergeben)
        Lieferungsposition.objects.create(
            lieferung=lieferung,
            geraetetyp=typ,
            geraetemodell=modell,
            farbe=str(row.get('Farbe') or '').strip(),
            speicher=str(row.get('Speicher') or '').strip(),
            ram=str(row.get('RAM') or '').strip(),
            prozessor=str(row.get('Prozessor') or '').strip(),
            zustand=str(row.get('Zustand') or '').strip(),
            menge=menge
        )

    # Zur Detail-Ansicht der zuletzt bearbeiteten Lieferung
    return redirect('lieferung_detail', pk=lieferung.liefernummer)
