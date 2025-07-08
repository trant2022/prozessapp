from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Auftrag, Auftragsposition, Lieferung, Lieferant
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
import datetime
import json

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
    total_ordered = lieferungen.aggregate(total=Sum("gesamtmenge"))["total"] or 0
    processed     = lieferungen.filter(effektives_datum__isnull=False).aggregate(total=Sum("gesamtmenge"))["total"] or 0
    # external_processed z.B. 0, falls Du später extern definiert
    external_processed = 0

    context = {
        "lieferungen": lieferungen,
        "lieferanten": lieferanten,
        "today": today,
        "kpi": {
            "total_ordered": total_ordered,
            "internal_processed": processed,
            "external_processed": external_processed,
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

@require_POST


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

