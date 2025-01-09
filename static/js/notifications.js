// static/js/notifications.js

// Fonction pour obtenir le token CSRF
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
 }
 
 // Configuration par défaut pour fetch avec CSRF token
 const fetchConfig = {
    headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json',
    },
    credentials: 'same-origin'  // Pour inclure les cookies
 };
 
 // Initialisation au chargement du DOM
 document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
    checkSubscriptionStatus();
    // Vérifier toutes les 5 minutes
    setInterval(checkSubscriptionStatus, 300000);
    // Vérifier les notifications toutes les 30 secondes
    setInterval(updateNotifications, 30000);
 });
 
 // Initialisation des notifications
 function initializeNotifications() {
    const notifTrigger = document.querySelector('.notifications-trigger');
    const notifMenu = document.querySelector('.notifications-menu');
 
    if (notifTrigger && notifMenu) {
        // Toggle du menu notifications
        notifTrigger.addEventListener('click', () => {
            notifMenu.classList.toggle('show');
            if (notifMenu.classList.contains('show')) {
                updateNotifications();
            }
        });
 
        // Fermer le menu si clic en dehors
        document.addEventListener('click', (e) => {
            if (!notifTrigger.contains(e.target) && !notifMenu.contains(e.target)) {
                notifMenu.classList.remove('show');
            }
        });
    }
 }
 
 // Mise à jour des notifications
 async function updateNotifications() {
    try {
        const response = await fetch('/api/notifications/unread/', {
            ...fetchConfig,
            method: 'GET'
        });
        
        if (response.status === 401) {
            window.location.href = '/login/';
            return;
        }
 
        const data = await response.json();
        const notifContent = document.querySelector('.notifications-content');
        const notifBadge = document.querySelector('.notification-badge');
        
        if (notifContent) {
            if (data.notifications.length > 0) {
                notifContent.innerHTML = data.notifications.map(notif => `
                    <div class="notification-item unread" data-id="${notif.id}">
                        <i class="ri-information-line"></i>
                        <div class="notification-details">
                            <p>${notif.message}</p>
                            <small>${notif.created_at}</small>
                        </div>
                        <button class="mark-read-btn" onclick="markAsRead(${notif.id})">
                            <i class="ri-check-line"></i>
                        </button>
                    </div>
                `).join('');
 
                // Mettre à jour le badge
                if (notifBadge) {
                    notifBadge.textContent = data.notifications.length;
                    notifBadge.classList.remove('hidden');
                }
            } else {
                notifContent.innerHTML = `
                    <div class="no-notifications">
                        <p>Pa gen notifikasyon</p>
                    </div>
                `;
                notifBadge?.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Erreur lors de la mise à jour des notifications:', error);
    }
 }
 
 // Marquer une notification comme lue
 async function markAsRead(notificationId) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/read/`, {
            ...fetchConfig,
            method: 'POST'
        });
 
        if (response.status === 401) {
            window.location.href = '/login/';
            return;
        }
 
        if (response.ok) {
            const notifItem = document.querySelector(`[data-id="${notificationId}"]`);
            if (notifItem) {
                notifItem.classList.add('fade-out');
                setTimeout(() => {
                    notifItem.remove();
                    updateNotifications();
                }, 300);
            }
        }
    } catch (error) {
        console.error('Erreur lors du marquage de la notification:', error);
    }
 }
 
 // Vérification du statut de l'abonnement
 async function checkSubscriptionStatus() {
    try {
        const response = await fetch('/api/subscription/status/', {
            ...fetchConfig,
            method: 'GET'
        });
 
        if (response.status === 401) {
            window.location.href = '/login/';
            return;
        }
 
        const data = await response.json();
        if (data) {
            updateSubscriptionUI(data);
        }
    } catch (error) {
        console.error('Erreur lors de la vérification de l\'abonnement:', error);
    }
 }
 
 // Mise à jour de l'interface utilisateur pour l'abonnement
 function updateSubscriptionUI(data) {
    const subsCard = document.querySelector('.subscription-status');
    if (!subsCard) return;
 
    let statusClass = '';
    let icon = '';
    let message = '';
 
    switch(data.status) {
        case 'expired':
            statusClass = 'status-expired';
            icon = 'ri-error-warning-line';
            message = 'Abònman w ekspire';
            break;
        case 'active':
            if (data.days_remaining <= 1) {
                statusClass = 'status-critical';
                icon = 'ri-timer-flash-line';
                message = `Abònman w ap ekspire nan ${data.days_remaining} jou`;
            } else if (data.days_remaining <= 3) {
                statusClass = 'status-warning';
                icon = 'ri-alarm-warning-line';
                message = `Abònman w ap ekspire nan ${data.days_remaining} jou`;
            } else if (data.days_remaining <= 7) {
                statusClass = 'status-notice';
                icon = 'ri-notification-line';
                message = `Abònman w ap ekspire nan ${data.days_remaining} jou`;
            } else {
                statusClass = 'status-good';
                icon = 'ri-checkbox-circle-line';
                message = 'Abònman w valid';
            }
            break;
        default:
            statusClass = 'status-expired';
            icon = 'ri-error-warning-line';
            message = 'Ou pa gen abònman aktif';
    }
 
    subsCard.className = `subscription-status ${statusClass}`;
    subsCard.innerHTML = `
        <i class="${icon}"></i>
        <p>${message}</p>
        ${data.end_date ? `<p class="subscription-details">Dat ekspirasyon: ${data.end_date}</p>` : ''}
    `;
 }
 
 // Gestionnaire d'erreur global pour les requêtes fetch
 window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.status === 401) {
        window.location.href = '/login/';
    }
 });