# views.py
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
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(driver=request.user)
            return Response(serializer.data)
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
#####################passenger app