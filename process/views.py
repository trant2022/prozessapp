from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Auftrag, Auftragsposition, Lieferung
import datetime

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
    # alle Lieferungen, sortiert nach Liefernummer
    lieferungen = Lieferung.objects.order_by('liefernummer')
    return render(request, 'process/dashboard.html', {
        'lieferungen': lieferungen
    })

def lieferung_angekommen(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    lieferung.mark_arrived()
    return redirect('dashboard')