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
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate
from app.serializers import UserSerializer, CustomTokenObtainPairSerializer


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
    
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

@permission_classes([IsAuthenticated])
class LogoutView(APIView):
    def post(self, request):
        try:
            # Vous pouvez ajouter ici la logique pour blacklister le token
            return Response({'message': 'Déconnexion réussie'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
class LoginView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Les champs username et password sont requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Identifiants invalides'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Ce compte est désactivé'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'user_type': user.user_type,
            }
        })
        
#####################passenger app