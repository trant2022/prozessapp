import pandas as pd
import datetime
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
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
    if request.method == "POST":
        lieferant_id     = request.POST.get("lieferant")
        erwartetes_datum = request.POST.get("erwartetes_datum")
        gesamtmenge      = request.POST.get("gesamtmenge")

        if lieferant_id and erwartetes_datum and gesamtmenge:
            supplier = get_object_or_404(Lieferant, pk=lieferant_id)
            Lieferung.objects.create(
                lieferant=supplier,
                bestelldatum=timezone.localdate(),
                erwartetes_datum=erwartetes_datum,
                gesamtmenge=int(gesamtmenge),
            )
        return redirect("lieferung_list")

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
        "lieferungen": lieferungen,
        "lieferanten": lieferanten,
        "kpi": {
            "devices_on_the_way": devices_on_the_way,
            "devices_arrived":    devices_arrived,
            "processed_internal": processed_internal,
            "processed_external": processed_external,
        },
    }
    return render(request, "process/order_list.html", context)

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

    for _, row in df.iterrows():
        nr = row.get('Liefernummer')
        if pd.isna(nr):
            continue
        try:
            lieferung = Lieferung.objects.get(liefernummer=int(nr))
        except Lieferung.DoesNotExist:
            continue

        typ_name = row.get('Gerätetyp') or row.get('Geraetetyp')
        if not typ_name or pd.isna(typ_name):
            continue
        typ, _ = Gerätetyp.objects.get_or_create(name=str(typ_name).strip())

        modell_name = row.get('Modell')
        if not modell_name or pd.isna(modell_name):
            continue
        modell, _ = Gerätemodell.objects.get_or_create(
            typ=typ,
            name=str(modell_name).strip()
        )

        pos_nr = row.get('Positionsnummer')
        if pd.isna(pos_nr):
            continue
        pos_nr = int(pos_nr)

        Lieferungsposition.objects.update_or_create(
            lieferung=lieferung,
            positionsnummer=pos_nr,
            defaults={
                'geraetetyp':   typ,
                'geraetemodell': modell,
                'farbe':        row.get('Farbe')    if not pd.isna(row.get('Farbe'))    else '',
                'speicher':     row.get('Speicher') if not pd.isna(row.get('Speicher')) else '',
                'ram':          row.get('RAM')      if not pd.isna(row.get('RAM'))      else '',
                'prozessor':    row.get('Prozessor')if not pd.isna(row.get('Prozessor'))else '',
                'zustand':      row.get('Zustand')  if not pd.isna(row.get('Zustand'))  else '',
                'menge':        int(row.get('Menge')) if not pd.isna(row.get('Menge'))  else 0,
            }
        )

    return redirect("lieferung_list")

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

    return render(request, 'process/lieferung_edit.html', {
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

    for _, row in df.iterrows():
        nr = row.get('Liefernummer')
        if pd.isna(nr):
            continue
        try:
            lieferung = Lieferung.objects.get(liefernummer=int(nr))
        except Lieferung.DoesNotExist:
            continue

        # Gerätetyp
        typ_name = row.get('Gerätetyp') or row.get('Geraetetyp')
        if not typ_name or pd.isna(typ_name):
            continue
        typ, _ = Gerätetyp.objects.get_or_create(name=str(typ_name).strip())

        # Modell
        modell_name = row.get('Modell')
        if not modell_name or pd.isna(modell_name):
            continue
        modell, _ = Gerätemodell.objects.get_or_create(
            typ=typ,
            name=str(modell_name).strip()
        )

        # Menge
        menge = row.get('Menge')
        menge = int(menge) if not pd.isna(menge) else 0

        # Wenn keine Positionsnummer in der Datei, einfach neues Objekt anlegen:
        pos_nr = row.get('Positionsnummer')
        if pd.isna(pos_nr):
            # Auto-Vergabe der positionsnummer durch Model.save()
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
        else:
            # Wenn doch vorhanden, update_or_create nutzen
            Lieferungsposition.objects.update_or_create(
                lieferung=lieferung,
                positionsnummer=int(pos_nr),
                defaults={
                    'geraetetyp':   typ,
                    'geraetemodell': modell,
                    'farbe':        str(row.get('Farbe') or '').strip(),
                    'speicher':     str(row.get('Speicher') or '').strip(),
                    'ram':          str(row.get('RAM') or '').strip(),
                    'prozessor':    str(row.get('Prozessor') or '').strip(),
                    'zustand':      str(row.get('Zustand') or '').strip(),
                    'menge':        menge,
                }
            )

    return redirect("lieferung_list")
