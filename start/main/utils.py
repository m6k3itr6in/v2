import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscriptions

def send_push_to_admin(title, body, url):
    subscriptions = PushSubscriptions.objects.filter(user__is_superuser=True)

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