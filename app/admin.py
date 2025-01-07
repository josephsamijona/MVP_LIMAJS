from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models 
from .models import User, Subscription, BusSchedule, BusLocation, TravelHistory, NFCCard, Schedule, Stop, Route, RouteStop

@admin.register(NFCCard)
class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('nfc_id', 'card_type', 'is_active', 'user_count', 'created_at')
    list_filter = ('card_type', 'is_active', 'created_at')
    search_fields = ('nfc_id',)
    date_hierarchy = 'created_at'
    
    actions = ['activate_cards', 'deactivate_cards']

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = "Users Associated"

    def activate_cards(self, request, queryset):
        queryset.update(is_active=True)
    activate_cards.short_description = "Activate selected cards"

    def deactivate_cards(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_cards.short_description = "Deactivate selected cards"










@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'get_nfc_info', 'subscription_status', 'is_active')
    list_filter = ('user_type', 'is_active', 'date_joined', 'nfc_card__card_type')
    search_fields = ('username', 'email', 'nfc_card__nfc_id', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Bus System Information', {
            'fields': ('user_type', 'nfc_card', 'phone_number')
        }),
    )

    actions = ['activate_users', 'deactivate_users']

    def get_nfc_info(self, obj):
        if obj.nfc_card:
            status_color = 'green' if obj.nfc_card.is_active else 'red'
            status_icon = '✓' if obj.nfc_card.is_active else '✗'
            return format_html(
                '<span style="color: {};">{} ({}) {}</span>',
                status_color,
                obj.nfc_card.nfc_id,
                obj.nfc_card.get_card_type_display(),
                status_icon
            )
        return format_html('<span style="color: gray;">No NFC Card</span>')
    get_nfc_info.short_description = "NFC Card"

    def subscription_status(self, obj):
        if obj.user_type != 'PASSENGER':
            return '-'
        subscription = Subscription.objects.filter(passenger=obj, is_active=True).first()
        if not subscription:
            return format_html('<span style="color: red;">No Active Subscription</span>')
        if subscription.end_date < timezone.now():
            return format_html('<span style="color: orange;">Expired</span>')
        return format_html('<span style="color: green;">Active until {}</span>', 
                         subscription.end_date.strftime('%Y-%m-%d'))
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"

    # Ajout de filtres personnalisés pour NFC
    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        return list_filter + ('nfc_card__is_active', 'nfc_card__card_type')

    # Personnalisation du formulaire pour l'édition
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'nfc_card' in form.base_fields:
            # Limiter aux cartes NFC actives et non assignées
            form.base_fields['nfc_card'].queryset = NFCCard.objects.filter(
                models.Q(is_active=True) & 
                (models.Q(users=None) | models.Q(users=obj))
            )
        return form

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'subscription_type', 'start_date', 'end_date', 'subscription_status', 'days_remaining')
    list_filter = ('subscription_type', 'is_active', 'start_date')
    search_fields = ('passenger__username', 'passenger__email')
    date_hierarchy = 'start_date'
    
    actions = ['renew_subscription_month', 'deactivate_subscriptions']

    def subscription_status(self, obj):
        if not obj.is_valid():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')

    def days_remaining(self, obj):
        if not obj.is_valid():
            return "0"
        remaining = (obj.end_date - timezone.now()).days
        return str(remaining) + " days"

    def renew_subscription_month(self, request, queryset):
        for subscription in queryset:
            if subscription.end_date < timezone.now():
                subscription.start_date = timezone.now()
            subscription.end_date = subscription.end_date + timezone.timedelta(days=30)
            subscription.is_active = True
            subscription.save()
    renew_subscription_month.short_description = "Renew subscriptions for 1 month"

@admin.register(BusSchedule)
class BusScheduleAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'departure_point', 'arrival_point', 'departure_time', 
                   'estimated_arrival_time', 'driver', 'is_active', 'view_passengers')
    list_filter = ('is_active', 'departure_time', 'driver')
    search_fields = ('route_name', 'departure_point', 'arrival_point', 'driver__username')
    
    actions = ['activate_schedules', 'deactivate_schedules']

    def view_passengers(self, obj):
        url = reverse('admin:app_travelhistory_changelist') + f'?schedule={obj.id}'
        return format_html('<a href="{}">View Passengers</a>', url)

@admin.register(BusLocation)
class BusLocationAdmin(admin.ModelAdmin):
    list_display = ('driver',  'formatted_location', 'timestamp')
    list_filter = ('driver', 'timestamp')
    date_hierarchy = 'timestamp'

    def formatted_location(self, obj):
        return format_html(
            '<a href="https://www.google.com/maps?q={},{}" target="_blank">View on Map</a>',
            obj.latitude, obj.longitude
        )
    formatted_location.short_description = 'Location'

@admin.register(TravelHistory)
class TravelHistoryAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'driver', 'schedule', 'scan_timestamp', 'location_link')
    list_filter = ('scan_timestamp', 'driver', 'schedule')
    search_fields = ('passenger__username', 'driver__username', 'schedule__route_name')
    date_hierarchy = 'scan_timestamp'

    def location_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">View Location</a>',
                obj.latitude, obj.longitude
            )
        return "No location data"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.user_type == 'DRIVER':
            return qs.filter(driver=request.user)
        return qs

    def has_add_permission(self, request):
        return request.user.user_type in ['ADMIN', 'DRIVER']

    def has_change_permission(self, request, obj=None):
        if request.user.user_type == 'ADMIN':
            return True
        if request.user.user_type == 'DRIVER' and obj:
            return obj.driver == request.user
        return False
    
    
    
@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
   list_display = ('name', 'order', 'description')
   list_editable = ('order',)
   search_fields = ('name', 'description')
   ordering = ('order',)

class RouteStopInline(admin.TabularInline):
   model = RouteStop
   extra = 1
   ordering = ('order',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
   list_display = ('name', 'direction', 'start_time', 'end_time', 'display_stops')
   list_filter = ('direction',)
   inlines = [RouteStopInline]

   def display_stops(self, obj):
       return ", ".join([str(stop) for stop in obj.stops.all().order_by('routestop__order')])
   display_stops.short_description = 'Arrêts'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
   list_display = ('route', 'stop', 'day_of_week', 'departure_time', 'arrival_time', 'is_active')
   list_filter = ('day_of_week', 'is_active', 'route')
   search_fields = ('route__name', 'stop__name')
   date_hierarchy = 'created_at'
   list_editable = ('is_active',)
   actions = ['activate_schedules', 'deactivate_schedules']

   def activate_schedules(self, request, queryset):
       queryset.update(is_active=True)
   activate_schedules.short_description = "Activer les horaires sélectionnés"

   def deactivate_schedules(self, request, queryset):
       queryset.update(is_active=False)
   deactivate_schedules.short_description = "Désactiver les horaires sélectionnés"

# Personnalisation de l'interface d'administration
admin.site.site_header = "Bus Management System"
admin.site.site_title = "BMS Admin Portal"
admin.site.index_title = "Welcome to Bus Management System"