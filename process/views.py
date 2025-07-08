from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Lieferung, Lieferant, Gerätetyp, Gerätemodell, Auftragsposition
import pandas as pd

def generate_supplier_number():
    last = Lieferant.objects.order_by('-pk').first()
    if last and last.nummer.isdigit():
        return str(int(last.nummer) + 1)
    return "1"

def order_list(request):
    # POST: neue Lieferung anlegen
    if request.method == "POST":
        lieferant_id     = request.POST.get("lieferant")
        erwartetes_datum = request.POST.get("erwartetes_datum") or None
        gesamtmenge      = request.POST.get("gesamtmenge")
        kommentar        = request.POST.get("kommentar", "")

        if lieferant_id and gesamtmenge:
            supplier = get_object_or_404(Lieferant, pk=lieferant_id)
            Lieferung.objects.create(
                lieferant=supplier,
                bestelldatum=timezone.localdate(),
                erwartetes_datum=erwartetes_datum,
                gesamtmenge=int(gesamtmenge),
                kommentar=kommentar
            )
        return redirect("order_list")

    # GET: Dashboard rendern
    lieferungen  = Lieferung.objects.all()
    lieferanten  = Lieferant.objects.all()
    # KPIs
    devices_on_the_way = Lieferung.objects.filter(effektives_datum__isnull=True).aggregate(total=Sum('gesamtmenge'))['total'] or 0
    devices_arrived    = Lieferung.objects.filter(effektives_datum__isnull=False).aggregate(total=Sum('gesamtmenge'))['total'] or 0
    processed_internal = devices_arrived  # gleich intern
    processed_external = 0                # später anpassen

    context = {
        "lieferungen": lieferungen,
        "lieferanten": lieferanten,
        "kpi": {
            "devices_on_the_way": devices_on_the_way,
            "devices_arrived": devices_arrived,
            "processed_internal": processed_internal,
            "processed_external": processed_external,
        }
    }
    return render(request, "process/order_list.html", context)

@require_POST
def create_lieferung(request):
    name = request.POST.get('lieferant_name')
    supplier, created = Lieferant.objects.get_or_create(
        name=name,
        defaults={'nummer': generate_supplier_number()}
    )
    Lieferung.objects.create(
        lieferant=supplier,
        bestelldatum=request.POST.get('bestelldatum') or timezone.localdate(),
        erwartetes_datum=request.POST.get('erwartetes_datum') or None,
        gesamtmenge=int(request.POST.get('gesamtmenge')),
        kommentar=request.POST.get('kommentar', '')
    )
    return redirect('order_list')

@require_POST
def lieferung_angekommen(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    lieferung.mark_arrived()
    return redirect("order_list")

def lieferung_edit(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    if request.method == 'POST':
        lieferung.bestelldatum     = request.POST.get('bestelldatum') or lieferung.bestelldatum
        lieferung.erwartetes_datum = request.POST.get('erwartetes_datum') or None
        lieferung.gesamtmenge      = int(request.POST.get('gesamtmenge') or lieferung.gesamtmenge)
        lieferung.kommentar        = request.POST.get('kommentar', lieferung.kommentar)
        lieferung.save()
        return redirect('order_list')
    return render(request, 'process/lieferung_edit.html', {
        'lieferung': lieferung,
        'lieferanten': Lieferant.objects.all(),
    })

@require_POST
def upload_positions(request):
    positions_file = request.FILES.get('positions_file')
    if not positions_file:
        return HttpResponseBadRequest("Keine Datei ausgewählt")

    import pandas as pd
    df = pd.read_excel(positions_file)

    for _, row in df.iterrows():
        auftragsnr = row.get('Auftragsnummer')
        try:
            auftrag = Auftrag.objects.get(auftragsnummer=auftragsnr)
        except Auftrag.DoesNotExist:
            continue

        # Gerätetyp und Modell wie gehabt
        typ, _    = Gerätetyp.objects.get_or_create(name=row.get('Gerätetyp'))
        modell, _ = Gerätemodell.objects.get_or_create(typ=typ, name=row.get('Modell'))

        # Auftragsposition richtig anlegen / updaten
        Auftragsposition.objects.update_or_create(
            auftrag=auftrag,
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

def lieferung_detail(request, pk):
    """Detail‐Seite: zeigt alle Positionen einer Lieferung"""
    lieferung = get_object_or_404(Lieferung, pk=pk)
    positionen = Auftragsposition.objects.filter(auftrag=lieferung).select_related('geraetetyp','geraetemodell')
    return render(request, 'process/lieferung_detail.html', {
        'lieferung': lieferung,
        'positionen': positionen,
    })