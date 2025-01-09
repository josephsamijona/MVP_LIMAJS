from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.timezone import now


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
    

class Stop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

class Route(models.Model):
    DIRECTION_CHOICES = [
        ('ALLER', 'Trajet Aller'),
        ('RETOUR', 'Trajet Retour')
    ]

    name = models.CharField(max_length=100)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    stops = models.ManyToManyField(Stop, through='RouteStop')

    def __str__(self):
        return f"{self.name} ({self.direction})"

class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # Ordre des arrêts dans ce trajet spécifique
    estimated_time = models.IntegerField()  # Temps estimé en minutes depuis le début du trajet

    class Meta:
        ordering = ['order']
        unique_together = [['route', 'order']]  # Un seul arrêt peut avoir un ordre spécifique dans un trajet

    def __str__(self):
        return f"{self.route.name} - {self.stop.name} (Stop {self.order})"

class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('MON', 'Lundi'),
        ('TUE', 'Mardi'),
        ('WED', 'Mercredi'),
        ('THU', 'Jeudi'),
        ('FRI', 'Vendredi'),
        ('SAT', 'Samedi'),
        ('SUN', 'Dimanche')
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    day_of_week = models.CharField(max_length=20, choices=DAYS_OF_WEEK)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for {self.route.name} - {self.stop.name} at {self.departure_time}"

    class Meta:
        ordering = ['departure_time']
        
        
class Notification(models.Model):
    """
    Table pour gérer les notifications des utilisateurs
    """
    NOTIFICATION_TYPES = [
        ('SUB_7_DAYS', 'Abònman w ap fini nan 7 jou'),  # L'abonnement finit dans 7 jours
        ('SUB_3_DAYS', 'Abònman w ap fini nan 3 jou'),  # L'abonnement finit dans 3 jours
        ('SUB_1_DAY', 'Abònman w ap fini demen'),       # L'abonnement finit demain
        ('SUB_TODAY', 'Abònman w ap fini jodi a'),      # L'abonnement finit aujourd'hui
        ('SUB_EXPIRED', 'Abònman w fini'),              # L'abonnement est terminé
        ('BUS_DELAY', 'Bus la an reta'),                # Le bus est en retard
        ('BUS_ARRIVAL', 'Bus la prèske rive'),          # Le bus arrive bientôt
        ('SYSTEM_UPDATE', 'Mizajou sistèm lan'),        # Mise à jour système
        ('ROUTE_CHANGE', 'Chanjman nan wout la'),       # Changement d'itinéraire
    ]

    user = models.ForeignKey(
        'User',  
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def mark_as_read(self):
        self.read = True
        self.save()

    def mark_email_as_sent(self):
        self.is_email_sent = True
        self.save()