from django.conf import settings

def user_role_processor(request):
    from main.views import get_user_role
    context = {}
    if request.user.is_authenticated:
        context['user_role'] = get_user_role(request.user)
    else:
        context['user_role'] = None
    
    context['vapid_public_key'] = getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', None)
    return context