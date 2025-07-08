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
    today = datetime.date.today()
    lieferungen = Lieferung.objects.order_by('liefernummer')
    lieferanten = Lieferant.objects.order_by('name')
    heute       = timezone.localdate()
    orders = (
        Auftrag.objects
        .filter(datensatz_importiert=False)
        .select_related('lieferant')
        .order_by('auftragsnummer')
    )

    total_ordered = orders.aggregate(sum=Sum('gesamtmenge'))['sum'] or 0
    processed_internal = (
        Auftrag.objects
        .filter(datensatz_importiert=True)
        .aggregate(sum=Sum('gesamtmenge'))['sum'] or 0
    )
    processed_external = (
        Auftrag.objects
        .filter(braendi_abgeholt__isnull=False)
        .aggregate(sum=Sum('gesamtmenge'))['sum'] or 0
    )

    return render(request, 'process/order_list.html', {
        'lieferungen': lieferungen,
        'lieferanten': lieferanten,
        'orders': orders,
        'today': heute,
        'kpi': {
            'total_ordered': total_ordered,
            'processed_internal': processed_internal,
            'processed_external': processed_external,
        }
    })

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
    if request.method == 'POST':
        # wenn neuer Lieferant angegeben, zuerst anlegen:
        neuer_name = request.POST.get('neuer_lieferant')
        if neuer_name:
            supplier = Lieferant.objects.create(
                nummer=generate_number(),
                name=neuer_name
            )
        else:
            supplier = Lieferant.objects.get(pk=request.POST['lieferant'])
        Lieferung.objects.create(
            lieferant=supplier,
            bestelldatum=datetime.date.today(),
            erwartetes_datum=request.POST['erwartetes_datum'],
            gesamtmenge=request.POST['gesamtmenge'],
        )
    return redirect('order_list')

def lieferung_angekommen(request, pk):
    if request.method == 'POST':
        lieferung = Lieferung.objects.get(pk=pk)
        lieferung.effektives_datum = datetime.date.today()
        lieferung.save()
    return redirect('order_list')
