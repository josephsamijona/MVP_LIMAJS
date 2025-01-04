from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """
    Extension du modèle User de Django pour inclure les informations spécifiques
    à notre système
    """
    USER_TYPES = [
        ('ADMIN', 'Administrator'),
        ('DRIVER', 'Bus Driver'),
        ('PASSENGER', 'Passenger')
    ]

    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPES,
        default='PASSENGER'
    )
    nfc_id = models.CharField(
        max_length=100, 
        unique=True, 
        null=True, 
        blank=True
    )
    phone_number = models.CharField(
        max_length=15, 
        null=True, 
        blank=True
    )
    is_active = models.BooleanField(default=True)

class Subscription(models.Model):
    """
    Gestion des abonnements des passagers
    """
    SUBSCRIPTION_TYPES = [
        ('MONTHLY', 'Monthly Pass'),
        ('QUARTERLY', 'Quarterly Pass'),
        ('ANNUAL', 'Annual Pass')
    ]

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'PASSENGER'}
    )
    subscription_type = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_TYPES
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and self.end_date > timezone.now()

class BusSchedule(models.Model):
    """
    Horaires des bus
    """
    route_name = models.CharField(max_length=100)
    departure_point = models.CharField(max_length=200)
    arrival_point = models.CharField(max_length=200)
    departure_time = models.TimeField()
    estimated_arrival_time = models.TimeField()
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'user_type': 'DRIVER'}
    )
    is_active = models.BooleanField(default=True)

class BusLocation(models.Model):
    """
    Suivi en temps réel de la position du bus
    """
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'DRIVER'}
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )
    timestamp = models.DateTimeField(auto_now=True)
    schedule = models.ForeignKey(
        BusSchedule,
        on_delete=models.CASCADE
    )

class TravelHistory(models.Model):
    """
    Historique des voyages (basé sur les scans NFC)
    """
    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='travel_histories',
        limit_choices_to={'user_type': 'PASSENGER'}
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='scanned_histories',
        limit_choices_to={'user_type': 'DRIVER'}
    )
    schedule = models.ForeignKey(
        BusSchedule,
        on_delete=models.CASCADE
    )
    scan_timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True
    )