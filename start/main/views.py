from django.shortcuts import render, redirect, get_object_or_404
from .models import CoffeeShop, Worker, Shift
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
import calendar
from datetime import date, timedelta

# Create your views here.
def index(request):
    cafes = CoffeeShop.objects.all()
    return render(request, 'main/index/index.html', {'cafes':cafes})

def get_workers(request, id):
    workers = Worker.objects.filter(coffee_shop_id=id)
    return render(request, 'main/workers/worker.html', {'workers':workers})

def schedule_view(request, coffee_shop_id, year=None, month=None):
    shop = get_object_or_404(CoffeeShop, id=coffee_shop_id)
    today = timezone.now().date()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    all_shops = CoffeeShop.objects.all()

    num_days = calendar.monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, num_days+1)]
    workers = Worker.objects.filter(coffee_shop=shop).filter(Q(fired_at__isnull=True) | Q(fired_at__gt=date(year, month, 1))).distinct()

    shifts = Shift.objects.filter(coffee_shop=shop, date__year=year, date__month=month)
    shifts_by_day_worker = {(s.worker_id, s.date): s for s in shifts}

    schedule = {}
    for worker in workers:
        schedule[worker] = []
        for day in days:
            shift = shifts_by_day_worker.get((worker.id, day))
            schedule[worker].append(shift)

    min_workers = shop.minimum_workers

    return render(request, 'main/schedule/schedule.html', {
        'shop':shop,
        'days':days,
        'workers':workers,
        'schedule':schedule,
        'min_workers':min_workers,
        'year':year,
        'month':month,
        'all_shops':all_shops,
    })