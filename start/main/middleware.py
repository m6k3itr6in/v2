from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_urls = [
            reverse('main:login'),
            reverse('main:register'),
            '/admin/',
        ]

        if not request.user.is_authenticated:
            if request.path not in allowed_urls and not (request.path.startswith('/static/') or request.path.startswith('/media/')):
                return redirect('main:login')
            return self.get_response(request)

        if request.user.is_authenticated and not request.user.is_superuser:
            from .models import Worker
            worker = Worker.objects.filter(user=request.user).first()
            
            if worker and not worker.coffee_shop and request.path != reverse('main:index') and request.path not in allowed_urls:
                if not (request.path.startswith('/static/') or request.path.startswith('/media/') or request.path == reverse('main:logout')):
                    return redirect('main:index')

        return self.get_response(request)