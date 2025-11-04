from django.shortcuts import render, redirect, get_object_or_404
from .models import CoffeeShop, Worker, Shift
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
import calendar
from datetime import date, timedelta, datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json

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

    schedule_rows = []
    for worker in workers:
        cells = []
        for idx, day in enumerate(days):
            cells.append({'date': day, 'shift': schedule[worker][idx]})
        schedule_rows.append({'worker': worker, 'cells': cells})

    min_workers = shop.minimum_workers

    # вычисления для навигации по месяцам
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    return render(request, 'main/schedule/schedule.html', {
        'shop':shop,
        'days':days,
        'workers':workers,
        'schedule':schedule,
        'schedule_rows':schedule_rows,
        'min_workers':min_workers,
        'year':year,
        'month':month,
        'all_shops':all_shops,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    })


@require_POST
@csrf_protect
def update_shift(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    worker_id = payload.get('worker_id')
    coffee_shop_id = payload.get('coffee_shop_id')
    date_str = payload.get('date')
    value_text = (payload.get('value') or '').strip()

    if not (worker_id and coffee_shop_id and date_str):
        return HttpResponseBadRequest('Missing required fields')

    try:
        worker = Worker.objects.get(id=worker_id)
        shop = CoffeeShop.objects.get(id=coffee_shop_id)
        day = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return HttpResponseBadRequest('Invalid identifiers')

    if value_text == '' or value_text.lower() in ('выходной', 'off', 'none'):
        Shift.objects.filter(worker=worker, date=day).delete()
        return JsonResponse({'ok': True, 'action': 'deleted'})

    if value_text == '+':
        shift, _created = Shift.objects.update_or_create(
            worker=worker,
            date=day,
            defaults={
                'coffee_shop': shop,
                'start_time': None,
                'another_shop': None,
                'is_plus': True,
            }
        )
        return JsonResponse({'ok': True, 'action': 'updated_plus'})

    normalized = value_text.replace('.', ':')
    if normalized and normalized[0].isdigit() and ':' in normalized:
        parts = normalized.split(':')
        if len(parts[0]) == 1:
            normalized = f"0{parts[0]}:{(parts[1] if len(parts) > 1 else '00')[:2]}"

    parsed_time = None
    try:
        parsed_time = datetime.strptime(normalized, '%H:%M').time()
    except Exception:
        parsed_time = None

    if parsed_time is not None:
        shift, _created = Shift.objects.update_or_create(
            worker=worker,
            date=day,
            defaults={
                'coffee_shop': shop,
                'start_time': parsed_time,
                'another_shop': None,
                'is_plus': False,
            }
        )
        return JsonResponse({'ok': True, 'action': 'updated_time', 'time': parsed_time.strftime('%H:%M')})

    try:
        other_shop = CoffeeShop.objects.get(short_code=value_text)
    except CoffeeShop.DoesNotExist:
        return HttpResponseBadRequest('Unknown value')

    shift, _created = Shift.objects.update_or_create(
        worker=worker,
        date=day,
        defaults={
            'coffee_shop': shop,
            'start_time': None,
            'another_shop': other_shop,
            'is_plus': False,
        }
    )
    return JsonResponse({'ok': True, 'action': 'updated_shop', 'short_code': other_shop.short_code})