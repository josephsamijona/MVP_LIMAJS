class BusTrackingMap {
    constructor() {
        // Initialisation de la carte
        this.map = null;
        this.markers = {};
        this.trajectories = {};
        
        // État du tracking
        this.isTracking = false;
        this.updateInterval = null;
        this.lastUpdate = null;

        // Configuration
        this.updateFrequency = 10000; // 10 secondes
        this.maxTrajectoryPoints = 10; // Nombre de points pour la trajectoire

        // Styles des marqueurs
        this.busIcon = L.divIcon({
            html: '<i class="fas fa-bus text-primary text-2xl"></i>',
            className: 'bus-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.init();
    }

    async init() {
        try {
            // Création de la carte
            this.map = L.map('map').setView([18.5333, -72.3333], 13); // Coordonnées d'Haïti

            // Ajout de la couche OpenStreetMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            // Vérifier si le tracking est disponible avant de démarrer
            const trackingStatus = await this.checkTrackingAvailability();
            if (trackingStatus.tracking_available) {
                this.startTracking();
            } else {
                this.showTrackingUnavailable(trackingStatus.message);
            }
        } catch (error) {
            console.error('Erreur lors de l\'initialisation de la carte:', error);
            this.showError('Erreur lors du chargement de la carte');
        }
    }

    async checkTrackingAvailability() {
        try {
            const response = await fetch('/api/bus/locations/');
            const data = await response.json();
            return {
                tracking_available: data.tracking_available,
                message: data.message || 'Service non disponible'
            };
        } catch (error) {
            console.error('Erreur lors de la vérification du service:', error);
            return {
                tracking_available: false,
                message: 'Erreur de connexion au service'
            };
        }
    }

    startTracking() {
        if (!this.isTracking) {
            this.isTracking = true;
            this.updateBusLocations();
            this.updateInterval = setInterval(() => this.updateBusLocations(), this.updateFrequency);
        }
    }

    stopTracking() {
        if (this.isTracking) {
            this.isTracking = false;
            clearInterval(this.updateInterval);
        }
    }

    async updateBusLocations() {
        try {
            const response = await fetch('/api/bus/locations/');
            const data = await response.json();

            if (!data.tracking_available) {
                this.stopTracking();
                this.showTrackingUnavailable(data.message);
                return;
            }

            this.lastUpdate = data.last_update;
            this.updateStatusIndicator(true);

            // Mise à jour des marqueurs et trajectoires
            data.locations.forEach(location => {
                this.updateBusMarker(location);
                this.updateBusTrajectory(location);
            });

            // Supprimer les bus qui ne sont plus actifs
            Object.keys(this.markers).forEach(driverId => {
                if (!data.locations.find(loc => loc.driver_id === parseInt(driverId))) {
                    this.removeBus(driverId);
                }
            });

        } catch (error) {
            console.error('Erreur lors de la mise à jour des positions:', error);
            this.updateStatusIndicator(false);
        }
    }

    updateBusMarker(location) {
        const { driver_id, driver_name, latitude, longitude } = location;
        
        if (this.markers[driver_id]) {
            // Mettre à jour la position du marqueur existant
            this.markers[driver_id].setLatLng([latitude, longitude]);
            this.markers[driver_id].setPopupContent(this.createPopupContent(location));
        } else {
            // Créer un nouveau marqueur
            const marker = L.marker([latitude, longitude], { icon: this.busIcon })
                .bindPopup(this.createPopupContent(location))
                .addTo(this.map);

            this.markers[driver_id] = marker;
        }
    }

    updateBusTrajectory(location) {
        const { driver_id, positions } = location;

        if (!this.trajectories[driver_id]) {
            this.trajectories[driver_id] = L.polyline([], {
                color: '#FF6B00',
                weight: 3,
                opacity: 0.6
            }).addTo(this.map);
        }

        // Mettre à jour la trajectoire
        const latLngs = positions.slice(-this.maxTrajectoryPoints).map(pos => [pos.latitude, pos.longitude]);
        this.trajectories[driver_id].setLatLngs(latLngs);
    }

    removeBus(driverId) {
        if (this.markers[driverId]) {
            this.map.removeLayer(this.markers[driverId]);
            delete this.markers[driverId];
        }
        if (this.trajectories[driverId]) {
            this.map.removeLayer(this.trajectories[driverId]);
            delete this.trajectories[driverId];
        }
    }

    createPopupContent(location) {
        const time = new Date(location.timestamp).toLocaleTimeString();
        return `
            <div class="bus-popup">
                <h3 class="font-bold">${location.driver_name}</h3>
                <p class="text-sm">Dernière mise à jour: ${time}</p>
            </div>
        `;
    }

    showTrackingUnavailable(message) {
        const statusElement = document.getElementById('tracking-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="glass-card bg-red-50">
                    <p class="text-red-600">${message}</p>
                </div>
            `;
        }
    }

    showError(message) {
        const statusElement = document.getElementById('tracking-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="glass-card bg-red-50">
                    <p class="text-red-600">${message}</p>
                </div>
            `;
        }
    }

    updateStatusIndicator(isConnected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = isConnected ? 'text-green-500' : 'text-red-500';
            statusElement.textContent = isConnected ? 'Connecté' : 'Déconnecté';
        }
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.busTrackingMap = new BusTrackingMap();
});