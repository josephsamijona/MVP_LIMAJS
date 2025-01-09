from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Subscription, Notification
from datetime import timedelta

@shared_task
def check_subscription_expirations():
    """Tâche principale qui vérifie les abonnements et déclenche les notifications"""
    current_date = timezone.now().date()
    
    # Récupérer tous les abonnements actifs et expirés
    subscriptions = Subscription.objects.filter(
        is_active=True
    ).select_related('passenger')

    for subscription in subscriptions:
        days_remaining = (subscription.end_date.date() - current_date).days
        end_date_formatted = subscription.end_date.strftime('%d/%m/%Y')
        
        if days_remaining == 7:
            notification_message = f"Chè kliyan, abònman w ap fini nan 7 jou ({end_date_formatted}). Tanpri pase nan biwo LIMAJS MOTORS S.A pou renouvle li pou w ka kontinye itilize sèvis nou yo san pwoblèm."
            create_subscription_notification(
                subscription.passenger,
                'SUB_7_DAYS',
                notification_message,
                subscription.subscription_type,
                end_date_formatted
            )
        elif days_remaining == 3:
            notification_message = f"Chè kliyan, abònman w ap fini nan 3 jou ({end_date_formatted}). Pa bliye pase nan biwo LIMAJS MOTORS S.A pou renouvle li pou w ka kontinye itilize sèvis nou yo san pwoblèm."
            create_subscription_notification(
                subscription.passenger,
                'SUB_3_DAYS',
                notification_message,
                subscription.subscription_type,
                end_date_formatted
            )
        elif days_remaining == 1:
            notification_message = f"Chè kliyan, abònman w ap fini demen ({end_date_formatted}). Tanpri pase nan biwo LIMAJS MOTORS S.A jodi a pou renouvle li pou w evite entèripsyon sèvis la."
            create_subscription_notification(
                subscription.passenger,
                'SUB_1_DAY',
                notification_message,
                subscription.subscription_type,
                end_date_formatted
            )
        elif days_remaining == 0:
            notification_message = f"Chè kliyan, abònman w ap fini jodi a ({end_date_formatted}). Tanpri pase nan biwo LIMAJS MOTORS S.A san pèdi tan pou renouvle li pou w evite entèripsyon sèvis la."
            create_subscription_notification(
                subscription.passenger,
                'SUB_TODAY',
                notification_message,
                subscription.subscription_type,
                end_date_formatted
            )
        elif days_remaining < 0:
            notification_message = f"Chè kliyan, abònman w ekspire depi {end_date_formatted}. Tanpri pase nan biwo LIMAJS MOTORS S.A touswit pou renouvle li pou w ka rekòmanse itilize sèvis nou yo."
            create_subscription_notification(
                subscription.passenger,
                'SUB_EXPIRED',
                notification_message,
                subscription.subscription_type,
                end_date_formatted
            )

@shared_task
def create_subscription_notification(user, notification_type, message, subscription_type, end_date):
    """Créer une notification et envoyer un email"""
    # Création de la notification dans la base de données
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message
    )

    # Configuration du template de l'email
    subject = "LIMAJS MOTORS S.A - Rapèl Abònman"
    email_message = f"""
    Bonjou {user.get_full_name()},

    {message}

    Enfòmasyon sou abònman w:
    - Tip abònman: {subscription_type}
    - Dat ekspirasyon: {end_date}

    ENPÒTAN: Nou swete tout bagay ap mache byen pou ou! N'ap raple w ke abònman w ap ekspire byento. Pou asire sèvis w kontinye san pwoblèm, tanpri renouvle abònman w avan dat ekspirasyon an.
    Si abònman w pa renouvle a tan, sistèm nou an pral otomatikman entèwonp sèvis la, e nou vle ede w evite nenpòt deranjman.
    Tanpri pase nan biwo nou oswa kontakte nou pou fè sa rapid e fasil. N'ap toujou la pou ede w!

    

    Pou plis enfòmasyon oswa asistans:
    Email: info@limajsmotors.com
    Telefòn: +509 xxxx-xxxx
    WhatsApp: +509 xxxx-xxxx

    Mèsi anpil pou konfyans ou ak koperasyon w.

    LIMAJS MOTORS S.A
    Sèvis Kliyantèl
    """

    # Envoi de l'email
    try:
        send_mail(
            subject=subject,
            message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        # Marquer l'email comme envoyé
        notification.is_email_sent = True
        notification.save()
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {user.email}: {str(e)}")