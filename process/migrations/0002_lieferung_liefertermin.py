# Generated by Django 5.2.3 on 2025-07-09 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lieferung',
            name='liefertermin',
            field=models.DateField(blank=True, null=True, verbose_name='Liefertermin'),
        ),
    ]
