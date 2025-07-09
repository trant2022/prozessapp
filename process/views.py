import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Lieferung, Lieferant, Gerätetyp, Gerätemodell, Lieferungsposition

def lieferung_list(request):
    # POST: neue Lieferung anlegen
    if request.method == "POST":
        l_id = request.POST.get("lieferant")
        ed   = request.POST.get("erwartetes_datum")
        gm   = request.POST.get("gesamtmenge")
        kom  = request.POST.get("kommentar", "")
        if l_id and gm:
            supplier = get_object_or_404(Lieferant, pk=l_id)
            Lieferung.objects.create(
                lieferant=supplier,
                bestelldatum=timezone.localdate(),
                erwartetes_datum=ed or None,
                gesamtmenge=int(gm),
                kommentar=kom
            )
        return redirect("order_list")

    lief = Lieferung.objects.all()
    # KPIs
    on_way = Lieferung.objects.filter(effektives_datum__isnull=True).aggregate(t=Sum('gesamtmenge'))['t'] or 0
    arrived = Lieferung.objects.filter(effektives_datum__isnull=False).aggregate(t=Sum('gesamtmenge'))['t'] or 0
    internal = arrived
    external = 0

    context = {
        "lieferungen": lief,
        "lieferanten": Lieferant.objects.all(),
        "kpi": {
            "devices_on_the_way": on_way,
            "devices_arrived": arrived,
            "processed_internal": internal,
            "processed_external": external,
        }
    }
    return render(request, "process/order_list.html", context)


def lieferung_detail(request, pk):
    lieferung = get_object_or_404(Lieferung, pk=pk)
    pos = lieferung.positionen.select_related('geraetetyp', 'geraetemodell')
    return render(request, "process/lieferung_detail.html", {
        "lieferung": lieferung,
        "positionen": pos
    })


@require_POST
def create_lieferung(request):
    name = request.POST.get('lieferant_name')
    supplier, _ = Lieferant.objects.get_or_create(
        name=name,
        defaults={'nummer': Lieferant.generate_number()}
    )
    Lieferung.objects.create(
        lieferant=supplier,
        bestelldatum=request.POST.get('bestelldatum'),
        erwartetes_datum=request.POST.get('erwartetes_datum') or None,
        gesamtmenge=int(request.POST.get('gesamtmenge')),
        kommentar=request.POST.get('kommentar', '')
    )
    return redirect("order_list")


@require_POST
def lieferung_angekommen(request, pk):
    l = get_object_or_404(Lieferung, pk=pk)
    l.mark_arrived()
    return redirect("order_list")


def lieferung_edit(request, pk):
    l = get_object_or_404(Lieferung, pk=pk)
    if request.method == "POST":
        l.bestelldatum = request.POST.get('bestelldatum') or l.bestelldatum
        l.erwartetes_datum = request.POST.get('erwartetes_datum') or None
        l.gesamtmenge = int(request.POST.get('gesamtmenge', l.gesamtmenge))
        l.kommentar = request.POST.get('kommentar', l.kommentar)
        l.save()
        return redirect("order_list")
    return render(request, "process/lieferung_edit.html", {
        "lieferung": l,
        "lieferanten": Lieferant.objects.all()
    })


@require_POST
def upload_positions(request):
    f = request.FILES.get('positions_file')
    if not f:
        return HttpResponseBadRequest("Keine Datei ausgewählt")
    df = pd.read_excel(f)
    for _, row in df.iterrows():
        nr = row.get('Liefernummer')
        try:
            l = Lieferung.objects.get(liefernummer=nr)
        except Lieferung.DoesNotExist:
            continue
        typ, _ = Gerätetyp.objects.get_or_create(name=row.get('Gerätetyp'))
        mod, _ = Gerätemodell.objects.get_or_create(typ=typ, name=row.get('Modell'))
        Lieferungsposition.objects.update_or_create(
            lieferung=l,
            positionsnummer=int(row.get('Positionsnummer')),
            defaults={
                'geraetetyp': typ,
                'geraetemodell': mod,
                'farbe': row.get('Farbe', ''),
                'speicher': row.get('Speicher', ''),
                'ram': row.get('RAM', ''),
                'prozessor': row.get('Prozessor', ''),
                'zustand': row.get('Zustand', ''),
                'menge': int(row.get('Menge') or 0),
            }
        )
    return redirect("order_list")
