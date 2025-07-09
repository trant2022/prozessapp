from django.db import models
from django.utils import timezone

class Lieferant(models.Model):
    nummer = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Lieferantennummer"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Lieferant"
    )

    class Meta:
        verbose_name = "Lieferant"
        verbose_name_plural = "Lieferanten"

    def __str__(self):
        return f"{self.name} ({self.nummer})"

    @staticmethod
    def generate_number():
        last = Lieferant.objects.order_by('-pk').first()
        if last and last.nummer.isdigit():
            return str(int(last.nummer) + 1)
        return "1"


class Lieferung(models.Model):
    liefernummer = models.AutoField(
        primary_key=True,
        verbose_name="Liefernummer"
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
        null=True, blank=True,
        verbose_name="Erwartetes Ankunftsdatum"
    )
    gesamtmenge = models.PositiveIntegerField(
        verbose_name="Menge Total"
    )
    effektives_datum = models.DateField(
        null=True, blank=True,
        verbose_name="Effektives Ankunftsdatum"
    )
    kommentar = models.TextField(
        blank=True, verbose_name="Kommentar"
    )

    class Meta:
        verbose_name = "Lieferauftrag"
        verbose_name_plural = "Lieferaufträge"
        ordering = ['liefernummer']

    def mark_arrived(self):
        self.effektives_datum = timezone.localdate()
        self.save()

    def __str__(self):
        return f"{self.liefernummer} – {self.lieferant.name}"


class Gerätetyp(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Gerätetyp")

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
    name = models.CharField(max_length=100, verbose_name="Modellbezeichnung")

    class Meta:
        unique_together = ("typ", "name")
        verbose_name = "Gerätemodell"
        verbose_name_plural = "Gerätemodelle"

    def __str__(self):
        return f"{self.typ} - {self.name}"


class Lieferungsposition(models.Model):
    lieferung = models.ForeignKey(
        Lieferung,
        on_delete=models.CASCADE,
        related_name="positionen",
        verbose_name="Lieferung"
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
        unique_together = ('lieferung', 'positionsnummer')
        ordering = ['positionsnummer']
        verbose_name = "Lieferungsposition"
        verbose_name_plural = "Lieferungspositionen"

    def save(self, *args, **kwargs):
        if not self.positionsnummer:
            last = Lieferungsposition.objects.filter(lieferung=self.lieferung).order_by('-positionsnummer').first()
            self.positionsnummer = last.positionsnummer + 1 if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lieferung.liefernummer} - Pos {self.positionsnummer}"
