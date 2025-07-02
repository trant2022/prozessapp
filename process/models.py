from django.db import models

class Supplier(models.Model):
    number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.number})"


class Customer(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class DeviceModel(models.Model):
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("device_type", "name")

    def __str__(self):
        return f"{self.device_type} - {self.name}"


class Order(models.Model):
    ORDER_TYPES = [
        ('BROKER', 'Broker'),
        ('RETAIL', 'Retail'),
        ('MARKETPLACE', 'Marketplace'),
    ]
    order_number = models.CharField(max_length=100, unique=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    net_price_fw = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    logistics_cost_fw = models.DecimalField(max_digits=12, decimal_places=2)
    currency_rate = models.DecimalField(max_digits=12, decimal_places=6)
    net_price_chf = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    total_quantity = models.PositiveIntegerField(editable=False)
    reserved_quantity = models.PositiveIntegerField()
    quantity_retail = models.PositiveIntegerField()
    quantity_broker = models.PositiveIntegerField()
    quantity_marketplace = models.PositiveIntegerField()
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    securaze_possible = models.BooleanField()
    dataset_received = models.BooleanField(default=False)
    dataset_imported = models.BooleanField(default=False)
    test_required = models.BooleanField()
    cleaning_choice = models.CharField(max_length=20, choices=[
        ('NO', 'Nein'),
        ('MINIMAL', 'Ja, minimal'),
        ('FULL', 'Ja, voll'),
    ])
    wipe_method = models.CharField(max_length=20, choices=[
        ('NO', 'Nein'),
        ('SMART_ERASURE', 'Smart Erasure'),
        ('DATA_CLEAR', 'Data Clear'),
    ])
    packaging = models.CharField(max_length=50, choices=[
        ('LARGE_BOX', 'Grosskarton'),
        ('FOLDING_BOX', 'Faltkarton'),
    ])
    sell_price_net = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    braendi_required = models.BooleanField()
    braendi_notified_at = models.DateField(null=True, blank=True)
    braendi_delivered_at = models.DateField(null=True, blank=True)
    braendi_collected_at = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Berechne total_quantity und net_price_chf automatisch
        total_qty = sum(pos.quantity for pos in self.positions.all()) if self.pk else 0
        self.total_quantity = total_qty
        if total_qty:
            self.net_price_chf = (self.net_price_fw + (self.logistics_cost_fw / total_qty)) * self.currency_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderPosition(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='positions')
    position_number = models.PositiveIntegerField()
    device_type = models.ForeignKey(DeviceType, on_delete=models.PROTECT)
    device_model = models.ForeignKey(DeviceModel, on_delete=models.PROTECT)
    color = models.CharField(max_length=50)
    storage = models.CharField(max_length=50)
    ram = models.CharField(max_length=50)
    processor = models.CharField(max_length=100)
    condition = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('order', 'position_number')
        ordering = ['position_number']

    def save(self, *args, **kwargs):
        if not self.position_number:
            last = OrderPosition.objects.filter(order=self.order).order_by('-position_number').first()
            self.position_number = last.position_number + 1 if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} - Pos {self.position_number}"
