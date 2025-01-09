import os
from celery import Celery
from celery.schedules import crontab

# Définir les variables d'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Créer l'instance Celery
app = Celery('config')

# Charger la configuration depuis Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'check-subscription-expirations': {
        'task': 'app.tasks.check_subscription_expirations',
        'schedule': crontab(hour=8, minute=0),
    },
}