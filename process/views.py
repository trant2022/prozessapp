from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Auftrag, Auftragsposition, Lieferung, Lieferant
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
import datetime
import json


def order_list(request):
    today = datetime.date.today()
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
        'orders': orders,
        'today': today,
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

def lieferung_angekommen(request, pk):
    if request.method == "POST":
        l = get_object_or_404(Lieferung, liefernummer=pk)
        l.effektives_datum = timezone.localdate()
        l.save()
    return redirect('dashboard')

def lieferung_neu(request):
    data = json.loads(request.body)
    lieferant_val = data.get('lieferant')
    # wenn Auswahl "__new__", lege neuen Lieferant an
    if lieferant_val == '__new__':
        name = data.get('new_supplier_name','').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Kein Name für neuen Lieferanten.'})
        # Nummer automatisch hochzählen lassen  
        letzte_nummer = Lieferant.objects.order_by('-id').first()
        nummer = f"{(letzte_nummer.id+1) if letzte_nummer else 1:03d}"
        supplier = Lieferant.objects.create(name=name, nummer=nummer)
    else:
        supplier = get_object_or_404(Lieferant, pk=int(lieferant_val))

    l = Lieferung.objects.create(
      lieferant=supplier,
      bestelldatum=data['bestelldatum'],
      erwartetes_datum=data['erwartetes_datum'],
      gesamtmenge=data['gesamtmenge'],
    )
    return JsonResponse({'success': True, 'liefernummer': l.liefernummer})