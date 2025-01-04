from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class NFCCard(models.Model):
    """
    Table pour gérer les cartes NFC et leurs types
    """
    NFC_TYPES = [
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
        ('EMPLOYEE', 'Employee')
    ]

    nfc_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="NFC ID"
    )
    card_type = models.CharField(
        max_length=10,
        choices=NFC_TYPES,
        verbose_name="Type de carte"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nfc_id} - {self.get_card_type_display()}"

    class Meta:
        verbose_name = "NFC Card"
        verbose_name_plural = "NFC Cards"


class User(AbstractUser):
    USER_TYPES = [
        ('ADMIN', 'Administrator'),
        ('DRIVER', 'Bus Driver'),
        ('PASSENGER', 'Passenger')
    ]

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPES,
        default='PASSENGER'
    )
    nfc_card = models.ForeignKey(
        NFCCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone_number = models.CharField(
        max_length=15, 
        null=True, 
        blank=True
    )

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