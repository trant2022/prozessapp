from django.db import models
from django.utils import timezone

class Lieferant(models.Model):
    nummer = models.CharField(max_length=50, unique=True, verbose_name="Lieferantennummer")
    name = models.CharField(max_length=200, verbose_name="Lieferant")

    class Meta:
        verbose_name = "Lieferant"
        verbose_name_plural = "Lieferanten"

    def __str__(self):
        return f"{self.name} ({self.nummer})"


class Kunde(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Kunde"
    )

    class Meta:
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"

    def __str__(self):
        return self.name


class Gerätetyp(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Gerätetyp"
    )

    class Meta:
        verbose_name = "Gerätetyp"
        verbose_name_plural = "Gerätetypen"

    def __str__(self):
        return self.name


class Gerätemodell(models.Model):
    typ = models.ForeignKey(
        Gerätetyp,
        on_delete=models.CASCADE,
        related_name="modelle",
        verbose_name="Gerätetyp"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Modellbezeichnung"
    )

    class Meta:
        unique_together = ("typ", "name")
        verbose_name = "Gerätemodell"
        verbose_name_plural = "Gerätemodelle"

    def __str__(self):
        return f"{self.typ} - {self.name}"


class Lieferung(models.Model):
    liefernummer = models.AutoField(
        primary_key=True,
        verbose_name="Liefernummer"
    )
    kommentar = models.TextField(
        blank=True, verbose_name="Kommentar"
        )
    lieferant = models.ForeignKey(
        Lieferant,
        on_delete=models.PROTECT,
        verbose_name="Lieferant"
    )
    bestelldatum = models.DateField(
        verbose_name="Bestelldatum"
    )
    erwartetes_datum = models.DateField(
        null=True,
        blank=True,
        verbose_name="Erwartetes Ankunftsdatum"
    )
    gesamtmenge = models.PositiveIntegerField(
        verbose_name="Menge Total"
    )
    kommentar = models.TextField(
        blank=True,
        verbose_name="Kommentar"
    )
    effektives_datum = models.DateField(
        null=True,
        blank=True,
        verbose_name="Effektives Ankunftsdatum"
    )

    class Meta:
        verbose_name = "Lieferauftrag"
        verbose_name_plural = "Lieferaufträge"
        ordering = ['liefernummer']

    def mark_arrived(self):
        """Setzt das effektive Datum auf heute."""
        self.effektives_datum = timezone.localdate()
        self.save()

    def __str__(self):
        return f"{self.liefernummer} – {self.lieferant.name}"



class Auftrag(models.Model):
    AUFTRAGSARTEN = [
        ('BROKER', 'Broker'),
        ('RETAIL', 'Retail'),
        ('MARKETPLACE', 'Marktplatz'),
    ]
    auftragsnummer = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Auftragsnummer"
    )
    auftragsart = models.CharField(
        max_length=20,
        choices=AUFTRAGSARTEN,
        verbose_name="Auftragsart"
    )
    lieferant = models.ForeignKey(
        Lieferant,
        on_delete=models.PROTECT,
        verbose_name="Lieferant"
    )
    kunde = models.ForeignKey(
        Kunde,
        on_delete=models.PROTECT,
        verbose_name="Kunde"
    )
    nettopreis_fw = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Nettopreis Fremdwährung"
    )
    waehrung = models.CharField(
        max_length=10,
        verbose_name="Währung"
    )
    logistikkosten_fw = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Logistikkosten Fremdwährung"
    )
    wechselkurs = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        verbose_name="Wechselkurs"
    )
    nettopreis_chf = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        verbose_name="Nettopreis CHF"
    )
    gesamtmenge = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True,
        verbose_name="Gesamtmenge"
    )
    reservierte_menge = models.PositiveIntegerField(
        verbose_name="Reservierte Menge"
    )
    menge_retail = models.PositiveIntegerField(
        verbose_name="Menge Retail"
    )
    menge_broker = models.PositiveIntegerField(
        verbose_name="Menge Broker"
    )
    menge_marktplatz = models.PositiveIntegerField(
        verbose_name="Menge Marktplatz"
    )
    bestelldatum = models.DateField(verbose_name="Bestelldatum")
    lieferdatum = models.DateField(
        null=True,
        blank=True,
        verbose_name="Erwartetes Lieferdatum"
    )
    sicherung_moeglich = models.BooleanField(verbose_name="Securaze möglich")
    datensatz_erhalten = models.BooleanField(
        default=False,
        verbose_name="Datensatz erhalten"
    )
    datensatz_importiert = models.BooleanField(
        default=False,
        verbose_name="Datensatz importiert"
    )
    test_noetig = models.BooleanField(verbose_name="Test erforderlich")
    reinigung = models.CharField(
        max_length=20,
        choices=[
            ('NO', 'Nein'),
            ('MINIMAL', 'Ja, minimal'),
            ('FULL', 'Ja, voll'),
        ],
        verbose_name="Reinigung"
    )
    loeschmethode = models.CharField(
        max_length=20,
        choices=[
            ('NO', 'Nein'),
            ('SMART_ERASURE', 'Smart Erasure'),
            ('DATA_CLEAR', 'Data Clear'),
        ],
        verbose_name="Löschmethode"
    )
    verpackung = models.CharField(
        max_length=50,
        choices=[
            ('LARGE_BOX', 'Grosskarton'),
            ('FOLDING_BOX', 'Faltkarton'),
        ],
        verbose_name="Verpackung"
    )
    verkaufspreis_netto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Verkaufspreis netto"
    )
    braendi_noetig = models.BooleanField(verbose_name="Brändi nötig")
    braendi_benachrichtigt = models.DateField(
        null=True,
        blank=True,
        verbose_name="Brändi benachrichtigt"
    )
    braendi_geliefert = models.DateField(
        null=True,
        blank=True,
        verbose_name="Brändi geliefert"
    )
    braendi_abgeholt = models.DateField(
        null=True,
        blank=True,
        verbose_name="Brändi abgeholt"
    )

    class Meta:
        verbose_name = "Auftrag"
        verbose_name_plural = "Aufträge"

    def save(self, *args, **kwargs):
        total_qty = (
            (self.reservierte_menge or 0)
            + (self.menge_retail or 0)
            + (self.menge_broker or 0)
            + (self.menge_marktplatz or 0)
        )
        self.gesamtmenge = total_qty
        if total_qty:
            unit_log = self.logistikkosten_fw / total_qty
            self.nettopreis_chf = (unit_log + self.nettopreis_fw) * self.wechselkurs
        else:
            self.nettopreis_chf = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.auftragsnummer


class Auftragsposition(models.Model):
    auftrag = models.ForeignKey(
        Auftrag,
        on_delete=models.CASCADE,
        related_name='positionen',
        verbose_name="Auftrag"
    )
    positionsnummer = models.PositiveIntegerField(verbose_name="Positionsnummer")
    geraetetyp = models.ForeignKey(
        Gerätetyp,
        on_delete=models.PROTECT,
        verbose_name="Gerätetyp"
    )
    geraetemodell = models.ForeignKey(
        Gerätemodell,
        on_delete=models.PROTECT,
        verbose_name="Gerätemodell"
    )
    farbe = models.CharField(max_length=50, verbose_name="Farbe")
    speicher = models.CharField(max_length=50, verbose_name="Speicher")
    ram = models.CharField(max_length=50, verbose_name="RAM")
    prozessor = models.CharField(max_length=100, verbose_name="Prozessor")
    zustand = models.CharField(max_length=100, verbose_name="Zustand")
    menge = models.PositiveIntegerField(verbose_name="Menge")

    class Meta:
        unique_together = ('auftrag', 'positionsnummer')
        ordering = ['positionsnummer']
        verbose_name = "Auftragsposition"
        verbose_name_plural = "Auftragspositionen"

    def save(self, *args, **kwargs):
        if not self.positionsnummer:
            last = Auftragsposition.objects.filter(
                auftrag=self.auftrag
            ).order_by('-positionsnummer').first()
            self.positionsnummer = last.positionsnummer + 1 if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.auftrag.auftragsnummer} - Pos {self.positionsnummer}"
