class NotificationManager {
    constructor() {
        // Sélection des éléments DOM
        this.notificationButton = document.getElementById('notifications');
        this.notificationCounter = document.querySelector('.notification-badge');
        this.notificationContainer = document.getElementById('notification-container');
        
        // Récupération du token CSRF
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // État des notifications
        this.unreadNotifications = [];
        this.isNotificationOpen = false;
        
        // Initialisation
        this.init();
    }

    async init() {
        // Ajouter les écouteurs d'événements
        this.notificationButton.addEventListener('click', () => this.toggleNotifications());
        
        // Première récupération des notifications
        await this.fetchNotifications();
        
        // Mettre en place la vérification périodique
        setInterval(() => this.fetchNotifications(), 30000); // Toutes les 30 secondes
    }

    async fetchNotifications() {
        try {
            const response = await fetch('/api/notifications/unread/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                }
            });

            if (!response.ok) throw new Error('Erreur lors de la récupération des notifications');

            const data = await response.json();
            this.unreadNotifications = data.notifications;
            this.updateNotificationBadge();
            
            if (this.isNotificationOpen) {
                this.renderNotifications();
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    updateNotificationBadge() {
        const count = this.unreadNotifications.length;
        if (count > 0) {
            this.notificationCounter.textContent = count > 99 ? '99+' : count;
            this.notificationCounter.classList.remove('hidden');
        } else {
            this.notificationCounter.classList.add('hidden');
        }
    }

    toggleNotifications() {
        this.isNotificationOpen = !this.isNotificationOpen;
        if (this.isNotificationOpen) {
            this.renderNotifications();
        } else {
            this.notificationContainer.classList.add('hidden');
        }
    }

    renderNotifications() {
        this.notificationContainer.classList.remove('hidden');
        
        if (this.unreadNotifications.length === 0) {
            this.notificationContainer.innerHTML = `
                <div class="glass-card notification-empty">
                    <p>Pas de nouvelles notifications</p>
                </div>`;
            return;
        }

        const notificationsHTML = this.unreadNotifications.map(notification => {
            let typeClass = '';
            // Définir la classe CSS selon le type de notification
            switch(notification.type) {
                case 'SUB_7_DAYS':
                case 'SUB_3_DAYS':
                case 'SUB_1_DAY':
                case 'SUB_TODAY':
                case 'SUB_EXPIRED':
                    typeClass = 'notification-subscription';
                    break;
                case 'BUS_DELAY':
                case 'BUS_ARRIVAL':
                    typeClass = 'notification-bus';
                    break;
                default:
                    typeClass = 'notification-system';
            }

            return `
                <div class="glass-card notification-item ${typeClass}" data-id="${notification.id}">
                    <p class="notification-message">${notification.message}</p>
                    <small class="notification-time">${this.formatNotificationTime(notification.created_at)}</small>
                    <button class="btn-mark-read" onclick="notificationManager.markAsRead(${notification.id})">
                        Marquer comme lu
                    </button>
                </div>`;
        }).join('');

        this.notificationContainer.innerHTML = notificationsHTML;
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error('Erreur lors du marquage de la notification');

            // Mise à jour locale des notifications
            this.unreadNotifications = this.unreadNotifications.filter(
                notif => notif.id !== notificationId
            );
            
            // Mettre à jour l'affichage
            this.updateNotificationBadge();
            this.renderNotifications();
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    formatNotificationTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Moins d'une heure
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
        }
        // Moins d'un jour
        else if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
        }
        // Plus d'un jour
        else {
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});