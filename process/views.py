from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Auftrag, Auftragsposition, Lieferung, Lieferant, Gerätetyp, Gerätemodell
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
import datetime
import json
import pandas as pd

def generate_number():
    # Liefert die bisher höchste numerische Lieferantennummer +1, oder "1" wenn noch keiner existiert.
    last = Lieferant.objects.order_by('-nummer').first()
    if last and last.nummer.isdigit():
        return str(int(last.nummer) + 1)
    return '1'


def order_list(request):
    # 1) POST: neue Lieferung anlegen
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
        return redirect("order_list")

    # 2) GET: Dashboard rendern
    lieferungen  = Lieferung.objects.all()
    lieferanten  = Lieferant.objects.all()
    today        = timezone.localdate()

    # KPI-Beispiele
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
    total_ordered = lieferungen.aggregate(total=Sum("gesamtmenge"))["total"] or 0
    processed     = lieferungen.filter(effektives_datum__isnull=False).aggregate(total=Sum("gesamtmenge"))["total"] or 0
    
    # external_processed z.B. 0, falls Du später extern definiert
    external_processed = 0

    context = {
        "lieferungen": lieferungen,
        "lieferanten": lieferanten,
        "today": today,
        "kpi": {
            "devices_on_the_way": devices_on_the_way,
            "devices_arrived":    devices_arrived,
            "processed_internal": processed,
            "processed_external": external_processed,
        }
    }

    return render(request, "process/order_list.html", context)


def order_detail(request, pk):
    order = get_object_or_404(Auftrag, pk=pk)
    positions = (
        order.positionen
        .select_related('geraetetyp', 'geraetemodell')
        .all()
    )
    return render(request, 'process/order_detail.html', {
        'order': order,
        'positions': positions,
    })

def dashboard(request):
    # alle offenen Lieferungen
    lieferungen = Lieferung.objects.all().order_by('liefernummer')
    # alle Lieferanten für das Dropdown
    suppliers = Lieferant.objects.all().order_by('name')
    # KPI 
    return render(request, 'process/order_list.html', {
        'orders': lieferungen,
        'suppliers': suppliers,
        'kpi': { 
          'total_ordered': 0,
          'processed_internal': 0,
          'processed_external': 0,
        }
    })

def lieferung_edit(request, pk):
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)

    if request.method == 'POST':
        # Formular-Felder aus POST ziehen und in das Model übernehmen
        # Bestelldatum darf manuell angepasst werden:
        lieferung.bestelldatum = request.POST.get('bestelldatum', lieferung.bestelldatum)
        # Erwartetes Datum ist optional:
        ed = request.POST.get('erwartetes_datum')
        lieferung.erwartetes_datum = ed if ed else None
        # Gesamtmenge manuell eingeben
        lieferung.gesamtmenge = int(request.POST.get('gesamtmenge', lieferung.gesamtmenge))
        # Kommentarfeld
        lieferung.kommentar = request.POST.get('kommentar', lieferung.kommentar)
        lieferung.save()
        return redirect('order_list')

    # GET → Rendern des Edit-Formulars
    return render(request, 'process/lieferung_edit.html', {
        'lieferung': lieferung,
        'lieferanten': Lieferant.objects.all(),
    })

def positionen_liste(request, pk):
    """
    Zeigt alle Auftragspositionen für die Lieferung mit der gegebenen PK.
    """
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)
    positionen = (
        lieferung.positionen
                 .select_related('geraetetyp', 'geraetemodell')
                 .all()
    )
    return render(request, 'process/positionen_liste.html', {
        'lieferung': lieferung,
        'positionen': positionen,
    })

@require_POST

def upload_positions(request):
    positions_file = request.FILES.get('positions_file')
    if not positions_file:
        return HttpResponseBadRequest("Keine Datei ausgewählt")
    # mit pandas auslesen
    df = pd.read_excel(positions_file)
    for _, row in df.iterrows():
        nr = row.get('Liefernummer')
        try:
            lieferung = Lieferung.objects.get(liefernummer=nr)
        except Lieferung.DoesNotExist:
            continue
        typ, _    = Gerätetyp.objects.get_or_create(name=row.get('Gerätetyp'))
        modell, _ = Gerätemodell.objects.get_or_create(typ=typ, name=row.get('Modell'))
        Auftragsposition.objects.update_or_create(
            auftrag=lieferung,
            positionsnummer=int(row.get('Positionsnummer')),
            defaults={
                'geraetetyp': typ,
                'geraetemodell': modell,
                'farbe': row.get('Farbe',''),
                'speicher': row.get('Speicher',''),
                'ram': row.get('RAM',''),
                'prozessor': row.get('Prozessor',''),
                'zustand': row.get('Zustand',''),
                'menge': int(row.get('Menge') or 0),
            }
        )
    return redirect('order_list')


def create_lieferung(request):
    if request.method == "POST":
        name = request.POST.get('lieferant_name')
        # Suche oder lege neu an
        supplier, created = Lieferant.objects.get_or_create(
            name=name,
            defaults={'nummer': generate_supplier_number()}
        )

        bestelldatum = request.POST.get('bestelldatum')
        erwartetes = request.POST.get('erwartetes_datum') or None
        menge = request.POST.get('gesamtmenge')
        kommentar = request.POST.get('kommentar', '')

        Lieferung.objects.create(
            lieferant=supplier,
            bestelldatum=bestelldatum,
            erwartetes_datum=erwartetes,
            gesamtmenge=menge,
            kommentar=kommentar
        )
        return redirect('order_list')

    # falls du das Formular auch per GET rendern möchtest
    lieferanten = Lieferant.objects.all()
    return render(request, 'process/order_list.html', {'lieferanten': lieferanten, 'lieferungen': Lieferung.objects.all(), 'kpi': {...}})


def lieferung_angekommen(request, pk):
    if request.method == "POST":
        lieferung = get_object_or_404(Lieferung, pk=pk)
        lieferung.mark_arrived()
    return redirect("order_list")

def generate_supplier_number():
    last = Lieferant.objects.order_by('-pk').first()
    if last and last.nummer.isdigit():
        return str(int(last.nummer) + 1)
    return "1"

