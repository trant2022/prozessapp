import json
import pandas as pd

from django.shortcuts             import render, get_object_or_404, redirect
from django.db.models             import Sum
from django.http                  import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils                  import timezone

from .models import (
    Lieferant,
    Lieferung,
    Gerätetyp,
    Gerätemodell,
    Lieferungsposition,
)


def generate_number():
    """
    Generiert eine neue Lieferantennummer, basierend auf der zuletzt
    angelegten Nummer (nur Ziffern).
    """
    last = Lieferant.objects.order_by('-nummer').first()
    if last and last.nummer.isdigit():
        return str(int(last.nummer) + 1)
    return '1'


def lieferung_list(request):
    """
    Zeigt das Dashboard mit allen Lieferungen und KPIs an.
    """
    lieferungen = Lieferung.objects.all()
    lieferanten = Lieferant.objects.all()

    devices_on_the_way = (
        Lieferung.objects
                  .filter(effektives_datum__isnull=True)
                  .aggregate(total=Sum('gesamtmenge'))['total']
        or 0
    )
    devices_arrived = (
        Lieferung.objects
                  .filter(effektives_datum__isnull=False)
                  .aggregate(total=Sum('gesamtmenge'))['total']
        or 0
    )

    context = {
        'lieferungen': lieferungen,
        'lieferanten': lieferanten,
        'kpi': {
            'devices_on_the_way': devices_on_the_way,
            'devices_arrived': devices_arrived,
            'processed_internal': devices_arrived,
            'processed_external': 0,
        },
        'today': timezone.localdate(),
    }
    return render(request, "process/order_list.html", context)


@require_POST
def create_lieferung(request):
    """
    Legt eine neue Lieferung an. POST-Parameter:
      - lieferant_name
      - bestelldatum
      - erwartetes_datum (optional)
      - liefertermin (optional)
      - gesamtmenge
      - kommentar (optional)
    """
    supplier_name    = request.POST.get('lieferant_name', '').strip()
    bestelldatum     = request.POST.get('bestelldatum')
    erwartetes_datum = request.POST.get('erwartetes_datum') or None
    liefertermin     = request.POST.get('liefertermin')   or None
    gesamtmenge      = request.POST.get('gesamtmenge')
    kommentar        = request.POST.get('kommentar', '')

    if supplier_name and bestelldatum and gesamtmenge:
        try:
            lieferant = Lieferant.objects.get(name=supplier_name)
        except Lieferant.DoesNotExist:
            return HttpResponseBadRequest(
                f"Lieferant „{supplier_name}“ existiert nicht."
            )

        Lieferung.objects.create(
            lieferant        = lieferant,
            bestelldatum     = bestelldatum,
            erwartetes_datum = erwartetes_datum,
            liefertermin     = liefertermin,
            gesamtmenge      = int(gesamtmenge),
            kommentar        = kommentar,
        )

    return redirect('lieferung_list')


@require_POST
def lieferung_angekommen(request, pk):
    """
    Markiert eine Lieferung als angekommen. Erwartet optional JSON-Body:
      { "delivered_quantity": <int> }
    und speichert diese Menge in `confirmed_menge`.
    """
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)

    # JSON payload auslesen
    try:
        payload = json.loads(request.body)
        qty = int(payload.get('delivered_quantity', 0))
        lieferung.confirmed_menge = qty
    except Exception:
        # kein gültiges JSON → ignorieren
        pass

    lieferung.mark_arrived()
    lieferung.save()
    return JsonResponse({'status': 'ok'})


@require_POST
def lieferung_loeschen(request, pk):
    """
    Löscht eine Lieferung vollständig.
    """
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)
    lieferung.delete()
    return JsonResponse({'status': 'ok'})


def lieferung_detail(request, pk):
    """
    Zeigt die Detailansicht einer einzelnen Lieferung an.
    """
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)
    return render(request, "process/lieferung_detail.html", {
        'lieferung': lieferung
    })


@require_http_methods(["GET", "POST"])
def lieferung_edit(request, pk):
    """
    GET  /lieferung/<pk>/bearbeiten/ → liefert JSON mit aktuellen Felddaten
    POST /lieferung/<pk>/bearbeiten/ → speichert die geänderten Felder
    """
    lieferung = get_object_or_404(Lieferung, liefernummer=pk)

    if request.method == 'POST':
        supplier = request.POST.get('lieferant_name', '').strip()
        lieferung.lieferant        = get_object_or_404(Lieferant, name=supplier)
        lieferung.bestelldatum     = request.POST.get('bestelldatum')
        lieferung.erwartetes_datum = request.POST.get('erwartetes_datum') or None
        lieferung.liefertermin     = request.POST.get('liefertermin')   or None
        lieferung.gesamtmenge      = int(request.POST.get('gesamtmenge', lieferung.gesamtmenge))
        lieferung.kommentar        = request.POST.get('kommentar', lieferung.kommentar)
        lieferung.save()
        return redirect('lieferung_list')

    # GET → JSON-Antwort für das Edit-Formular
    data = {
        'lieferant':        lieferung.lieferant.name,
        'bestelldatum':     lieferung.bestelldatum.isoformat(),
        'erwartetes_datum': lieferung.erwartetes_datum.isoformat() if lieferung.erwartetes_datum else '',
        'liefertermin':     lieferung.liefertermin.isoformat()   if lieferung.liefertermin   else '',
        'gesamtmenge':      lieferung.gesamtmenge,
        'kommentar':        lieferung.kommentar,
    }
    return JsonResponse(data)


@require_POST
def upload_positions(request):
    """
    Liest ein Excel ein und legt für jede Zeile eine
    Lieferungsposition an (automatisch nummeriert).
    """
    positions_file = request.FILES.get('positions_file')
    if not positions_file:
        return HttpResponseBadRequest("Keine Datei ausgewählt")

    try:
        df = pd.read_excel(positions_file)
    except Exception as e:
        return HttpResponseBadRequest(f"Dateilesefehler: {e}")

    lieferung = None
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

        # Basis-Felder
        menge = row.get('Menge')
        menge = int(menge) if not pd.isna(menge) else 0

        # Zusätzliche Felder
        def _txt(col):
            val = row.get(col)
            return str(val).strip() if not pd.isna(val) else ''

        Lieferungsposition.objects.create(
            lieferung                     = lieferung,
            geraetetyp                    = typ,
            geraetemodell                 = modell,
            farbe                         = _txt('Farbe'),
            speicher                      = _txt('Speicher'),
            ram                           = _txt('RAM'),
            prozessor                     = _txt('Prozessor'),
            zustand                       = _txt('Zustand'),
            menge                         = menge,
            auftragsart                   = _txt('Auftragsart'),
            kundenart                     = _txt('Kundenart'),
            kunde                         = _txt('Kunde'),
            ek_netto_fw                   = _txt('EK netto FW'),
            waehrung                      = _txt('Währung'),
            logistikkosten_geraet_fw      = _txt('Logistikkosten Gerät FW'),
            waehrungskurs                 = _txt('Währungskurs'),
            ek_netto_chf                  = _txt('EK netto CHF'),
            verpackungskosten             = _txt('Verpackungskosten'),
            wkz                           = _txt('WKZ'),
            vk_netto_geraet               = _txt('VK netto Gerät'),
            menge_reserve                 = _txt('Menge Reserve'),
            menge_retail                  = _txt('Menge Retail'),
            menge_broker                  = _txt('Menge Broker'),
            menge_marketplace             = _txt('Menge Marketplace'),
            menge_recycling               = _txt('Menge Recycling'),
            securaze_moeglich             = _txt('Securaze möglich'),
            datensatz_erhalten            = _txt('Datensatz erhalten'),
            datensatz_eingepflegt         = _txt('Datensatz eingepflegt'),
            testen                        = _txt('Testen'),
            putzen                        = _txt('Putzen'),
            loeschen                      = _txt('Löschen'),
            verpackung                    = _txt('Verpackung'),
            braendi                       = _txt('Braendi'),
            lieferart                     = _txt('Lieferart'),
            versanddienstleister          = _txt('Versanddienstleister'),
        )

    # Wenn mindestens eine Position importiert wurde, zurück zur Detail-Seite
    if lieferung:
        return redirect('lieferung_detail', pk=lieferung.liefernummer)
    return redirect('lieferung_list')
