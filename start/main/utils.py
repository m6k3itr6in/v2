import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from .models import PushSubscriptions

def send_push_notification(user, title, body, url):
    subscriptions = PushSubscriptions.objects.filter(user=user)
    
    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url
    })

    for sub in subscriptions:
        try:
            from urllib.parse import urlparse
            parsed_uri = urlparse(sub.endpoint)
            audience = f"{parsed_uri.scheme}://{parsed_uri.netloc}"

            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"auth": sub.auth, "p256dh": sub.p256dh}
                },
                data=payload,
                vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.WEBPUSH_ADMIN_EMAIL}",
                    "aud": audience
                },
                ttl=3600
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code == 410:
                sub.delete()

def send_push_to_admin(title, body, url, coffee_shop=None):
    if coffee_shop:
        admins = User.objects.filter(
            admin_shops__coffee_shop=coffee_shop
        ).distinct()
    else:
        admins = User.objects.filter(
            Q(is_superuser=True) | Q(profile__role='SUPER_ADMIN')
        ).distinct()
    
    for admin in admins:
        send_push_notification(admin, title, body, url)

def check_and_notify_understaffing():
    from .models import CoffeeShop, Shift
    from django.utils import timezone
    from datetime import timedelta
    
    target_date = timezone.localdate() + timedelta(days=2)
    shops = CoffeeShop.objects.all()
    
    for shop in shops:
        shifts_count = Shift.objects.filter(
            Q(coffee_shop=shop) | Q(another_shop=shop),
            date=target_date
        ).count()
        
        if shifts_count < shop.minimum_workers:
            title = "Нехватка персонала"
            body = f"На {shop.name}, {target_date.strftime('%d.%m')}, нехватает людей (в графике {shifts_count} из {shop.minimum_workers})."
            url = f"{settings.SITE_URL}/schedule/{shop.slug}/{target_date.year}/{target_date.month}/"
            
            send_push_to_admin(title, body, url)
            
            send_push_to_admin(title, body, url, coffee_shop=shop)