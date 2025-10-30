from django.shortcuts import render, redirect
from .models import CoffeeShop, Worker
from django.shortcuts import get_object_or_404

# Create your views here.
def index(request):
    cafes = CoffeeShop.objects.all()
    return render(request, 'main/index/index.html', {'cafes':cafes})

def get_workers(request, id):
    workers = Worker.objects.filter(coffee_shop_id=id)
    return render(request, 'main/workers/worker.html', {'workers':workers})