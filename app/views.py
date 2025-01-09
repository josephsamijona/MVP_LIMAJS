# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from datetime import datetime, timedelta
from rest_framework import viewsets, status,views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .models import NFCCard, User, TravelHistory, BusLocation
from .serializers import LocationUpdateSerializer, TravelHistorySerializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate
from app.serializers import DriverTokenObtainPairSerializer, DriverSerializer
from app.permissions import IsDriver
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.forms import PassengerLoginForm
from django.views.decorators.http import require_http_methods
from app.models import (
    Subscription,
    TravelHistory,
    Schedule,
    BusLocation,
    Route,
    Stop,
    #Notification
)

from django.views.generic import ListView

from datetime import datetime, time


###########DRIVER APP###
class DriverViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def verify_nfc(self, request):
        nfc_id = request.data.get('nfc_id')
        try:
            nfc_card = NFCCard.objects.get(nfc_id=nfc_id, is_active=True)
            passenger = User.objects.get(nfc_card=nfc_card)
            
            # Créer l'historique de voyage
            TravelHistory.objects.create(
                passenger=passenger,
                driver=request.user,
                schedule=request.data.get('schedule'),
                latitude=request.data.get('latitude'),
                longitude=request.data.get('longitude')
            )
            return Response({'valid': True, 'user': passenger.username})
        except NFCCard.DoesNotExist:
            return Response({'valid': False, 'error': 'Invalid NFC card'})

    @action(detail=False, methods=['post'])
    def update_location(self, request):
        print("Données reçues:", request.data)  # Pour le debugging
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(driver=request.user)
            return Response(serializer.data)
        print("Erreurs de validation:", serializer.errors)  # Pour le debugging
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def today_passengers(self, request):
        today = timezone.now().date()
        histories = TravelHistory.objects.filter(
            driver=request.user,
            scan_timestamp__date=today
        )
        serializer = TravelHistorySerializer(histories, many=True)
        return Response(serializer.data)
    
    
class DriverLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = DriverTokenObtainPairSerializer

class DriverProfileView(views.APIView):
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get(self, request):
        serializer = DriverSerializer(request.user)
        return Response(serializer.data)

class DriverLogoutView(views.APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(
                    {'message': 'Déconnexion réussie'}, 
                    status=status.HTTP_200_OK
                )
            return Response(
                {'error': 'Token de rafraîchissement requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except TokenError:
            return Response(
                {'error': 'Token invalide ou expiré'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class DriverTokenRefreshView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        try:
            token = RefreshToken(refresh_token)
            user = User.objects.get(id=token.payload.get('user_id'))
            
            if user.user_type != 'DRIVER':
                raise Exception('Token non valide pour un chauffeur')

            return Response({
                'access': str(token.access_token),
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
#####################passenger app#######################################
def passenger_login(request):
    if request.user.is_authenticated:
        return redirect('passenger_dashboard')
        
    if request.method == 'POST':
        form = PassengerLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            
            if user and user.user_type == 'PASSENGER':
                login(request, user)
                return redirect('passenger_dashboard')
            else:
                form.add_error(None, 'Invalid credentials or not a passenger account')
    else:
        form = PassengerLoginForm()
    
    return render(request, 'passenger/login.html', {'form': form})

@login_required
def passenger_logout(request):
    logout(request)
    return redirect('passenger_login')


class PassengerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'passenger/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        current_time = timezone.now()
        current_weekday = current_time.strftime('%A')[:3].upper()  # MON, TUE, etc.
        
        # Récupération de l'abonnement actif
        subscription = user.subscription_set.filter(
            is_active=True,
            end_date__gte=current_time
        ).last()
        context['subscription'] = subscription

        # Vérification si l'abonnement nécessite une notification
        if subscription:
            days_remaining = (subscription.end_date.date() - current_time.date()).days
            context['days_remaining'] = days_remaining
            
            # Status de l'abonnement pour l'interface
            if days_remaining <= 0:
                context['subscription_status'] = 'expired'
            elif days_remaining <= 1:
                context['subscription_status'] = 'critical'
            elif days_remaining <= 3:
                context['subscription_status'] = 'warning'
            elif days_remaining <= 7:
                context['subscription_status'] = 'notice'
            else:
                context['subscription_status'] = 'good'
        
        # Récupération des 5 derniers voyages
        context['recent_travels'] = user.travel_histories.all().select_related(
            'schedule', 
            'driver'
        ).order_by('-scan_timestamp')[:5]
        
        # Récupération des horaires du jour
        today_schedules = Schedule.objects.filter(
            day_of_week=current_weekday,
            is_active=True,
            departure_time__gte=current_time.time()  # Seulement les horaires à venir
        ).select_related(
            'route', 
            'stop'
        ).order_by('departure_time')
        context['today_schedules'] = today_schedules[:10]  # Limiter aux 10 prochains départs
        
        # Récupération des bus en service actuellement
        active_buses = BusLocation.objects.filter(
            driver__busschedule__is_active=True,
            timestamp__gte=current_time - timedelta(minutes=5)  # Seulement les positions récentes (5 dernières minutes)
        ).select_related(
            'driver'
        ).distinct()
        context['active_buses'] = active_buses
        
        # Récupération des notifications par type
        notifications = user.notifications.filter(read=False).order_by('-created_at')
        
        # Grouper les notifications par type
        context['subscription_notifications'] = notifications.filter(
            notification_type__in=['SUB_7_DAYS', 'SUB_3_DAYS', 'SUB_1_DAY', 'SUB_TODAY', 'SUB_EXPIRED']
        )
        context['bus_notifications'] = notifications.filter(
            notification_type__in=['BUS_DELAY', 'BUS_ARRIVAL']
        )
        context['system_notifications'] = notifications.filter(
            notification_type__in=['SYSTEM_UPDATE', 'ROUTE_CHANGE']
        )
        
        # Compteur total des notifications non lues
        context['unread_count'] = notifications.count()
        
        return context
    


class RouteScheduleView(LoginRequiredMixin, ListView):
   template_name = 'passenger/schedules.html'
   model = Schedule
   context_object_name = 'schedules'

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       current_time = timezone.now()
       current_weekday = current_time.strftime('%A')[:3].upper()  # MON, TUE, etc.

       # Définition des tranches horaires
       morning_start = time(5, 0)  # 5h du matin
       morning_end = time(12, 0)   # 12h 
       afternoon_start = time(12, 0) # 12h
       afternoon_end = time(19, 0)  # 19h

       # Récupération de tous les itinéraires actifs
       routes = Route.objects.all()
       context['routes'] = routes

       # Récupération des horaires du matin
       context['morning_schedules'] = Schedule.objects.filter(
           day_of_week=current_weekday,
           is_active=True,
           departure_time__gte=morning_start,
           departure_time__lt=morning_end
       ).select_related(
           'route',
           'stop'
       ).order_by('route', 'departure_time')

       # Récupération des horaires de l'après-midi
       context['afternoon_schedules'] = Schedule.objects.filter(
           day_of_week=current_weekday,
           is_active=True,
           departure_time__gte=afternoon_start,
           departure_time__lt=afternoon_end
       ).select_related(
           'route',
           'stop'
       ).order_by('route', 'departure_time')

       # Obtenir le jour actuel en créole
       days_in_creole = {
           'MON': 'Lendi',
           'TUE': 'Madi', 
           'WED': 'Mèkredi',
           'THU': 'Jedi',
           'FRI': 'Vandredi',
           'SAT': 'Samdi',
           'SUN': 'Dimanch'
       }
       context['current_day'] = days_in_creole.get(current_weekday, current_weekday)
       
       # Informations sur la tranche horaire actuelle
       current_time_obj = current_time.time()
       if morning_start <= current_time_obj < morning_end:
           context['current_period'] = 'morning'
       elif afternoon_start <= current_time_obj < afternoon_end:
           context['current_period'] = 'afternoon'
       else:
           context['current_period'] = 'closed'

       # Informations supplémentaires pour l'interface
       context['morning_range'] = f"{morning_start.strftime('%H:%M')} - {morning_end.strftime('%H:%M')}"
       context['afternoon_range'] = f"{afternoon_start.strftime('%H:%M')} - {afternoon_end.strftime('%H:%M')}"

       return context

   def get_queryset(self):
       current_weekday = timezone.now().strftime('%A')[:3].upper()
       return Schedule.objects.filter(
           day_of_week=current_weekday,
           is_active=True
       ).select_related(
           'route',
           'stop'
       ).order_by('departure_time')

class TravelHistoryView(LoginRequiredMixin, ListView):
   template_name = 'passenger/travel_history.html'
   model = TravelHistory
   context_object_name = 'travels'
   paginate_by = 10  # 10 voyages par page

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       
       # Récupérer les paramètres de filtre de l'URL
       filter_period = self.request.GET.get('period', 'all')
       current_date = timezone.now().date()

       # Statistiques générales
       total_travels = self.get_queryset().count()
       context['total_travels'] = total_travels

       # Voyages des 7 derniers jours
       last_week_travels = self.get_queryset().filter(
           scan_timestamp__date__gte=current_date - timedelta(days=7)
       ).count()
       context['last_week_travels'] = last_week_travels

       # Voyages du mois en cours
       current_month_travels = self.get_queryset().filter(
           scan_timestamp__month=current_date.month,
           scan_timestamp__year=current_date.year
       ).count()
       context['current_month_travels'] = current_month_travels

       # Informations sur les filtres actifs
       context['current_filter'] = filter_period
       context['filter_options'] = [
           {'value': 'today', 'label': 'Jodi a'},
           {'value': 'week', 'label': '7 dènye jou'},
           {'value': 'month', 'label': 'Mwa sa'},
           {'value': 'all', 'label': 'Tout vwayaj'}
       ]

       # Dates pour l'interface
       context['current_date'] = current_date
       context['week_ago'] = current_date - timedelta(days=7)
       context['month_start'] = current_date.replace(day=1)

       return context

   def get_queryset(self):
       queryset = TravelHistory.objects.filter(
           passenger=self.request.user
       ).select_related(
           'schedule',
           'driver'
       )

       # Filtre par période
       filter_period = self.request.GET.get('period', 'all')
       current_date = timezone.now().date()

       if filter_period == 'today':
           queryset = queryset.filter(scan_timestamp__date=current_date)
       elif filter_period == 'week':
           queryset = queryset.filter(
               scan_timestamp__date__gte=current_date - timedelta(days=7)
           )
       elif filter_period == 'month':
           queryset = queryset.filter(
               scan_timestamp__month=current_date.month,
               scan_timestamp__year=current_date.year
           )

       return queryset.order_by('-scan_timestamp')