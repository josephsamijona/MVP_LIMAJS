# Ce fichier doit être modifié pour inclure celery
from config.celery import app as celery_app

__all__ = ('celery_app',)