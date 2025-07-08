from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Auftrag, Auftragsposition, Lieferung, Lieferant
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
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
    lieferanten = Lieferant.objects.all()
    lieferungen = Lieferung.objects.order_by('liefernummer')
    return render(request, 'process/order_list.html', {
        'lieferanten': lieferanten,
        'orders': lieferungen,  # oder wie auch immer deine Daten heißen
    })

def lieferung_angekommen(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    lieferung.mark_arrived()
    return redirect('dashboard')

def lieferung_neu(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Nur POST erlaubt")
    try:
        payload = json.loads(request.body)
        l = Lieferant.objects.get(pk=payload['lieferant'])
        lieferung = Lieferung.objects.create(
            lieferant=l,
            bestelldatum=timezone.localdate(),
            erwartetes_datum=payload['erwartetes_datum'],
            gesamtmenge=payload['gesamtmenge']
        )
        return JsonResponse({'success': True, 'liefernummer': lieferung.liefernummer})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})