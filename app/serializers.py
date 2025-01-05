# serializers.py
from rest_framework import serializers
from .models import User, NFCCard, TravelHistory, BusLocation
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


##############DRIVER APP

class NFCCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFCCard
        fields = ['nfc_id', 'card_type', 'is_active']

class TravelHistorySerializer(serializers.ModelSerializer):
    passenger_details = serializers.SerializerMethodField()

    class Meta:
        model = TravelHistory
        fields = ['id', 'passenger', 'passenger_details', 'schedule', 
                 'scan_timestamp', 'latitude', 'longitude']

    def get_passenger_details(self, obj):
        return {
            'username': obj.passenger.username,
            'card_type': obj.passenger.nfc_card.card_type
        }

class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusLocation
        fields = ['latitude', 'longitude', 'schedule']
        
        
        
class DriverTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.user_type != 'DRIVER':
            raise serializers.ValidationError(
                {'error': 'Seuls les chauffeurs peuvent se connecter à cette application'}
            )
        
        # Ajouter des informations supplémentaires au token
        data.update({
            'user_id': self.user.id,
            'username': self.user.username,
            'user_type': self.user.user_type,
        })
        return data

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'user_type')
        read_only_fields = fields