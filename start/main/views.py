from django.shortcuts import render, redirect, get_object_or_404
from .models import CoffeeShop, Worker, Shift
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
import calendar
from datetime import date, timedelta, datetime
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json

def sync_workers_experience_years(workers):
    today = timezone.localdate()
    to_update = []
    for w in workers:
        if w.sync_experience_years(as_of=today, save=False):
            to_update.append(w)
    if to_update:
        Worker.objects.bulk_update(to_update, ["experience_years"])

def index(request):
    cafes = CoffeeShop.objects.all()
    return render(request, 'main/index/index.html', {'cafes':cafes})

def get_workers(request, slug):
    shop = get_object_or_404(CoffeeShop, slug=slug)
    workers = list(Worker.objects.filter(coffee_shop=shop))
    sync_workers_experience_years(workers)
    return render(request, 'main/shops/shops.html', {'workers':workers, 'shop':shop})


def worker_detail(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)
    worker.sync_experience_years(as_of=timezone.localdate(), save=True)
    return render(request, 'main/workers/worker.html', {'worker': worker})

def get_month_days(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, d) for d in range(1, num_days + 1)]


def get_active_workers(shop, year, month):
    month_start = date(year, month, 1)
    return Worker.objects.filter(
        coffee_shop=shop
    ).filter(
        Q(fired_at__isnull=True) | Q(fired_at__gt=month_start)
    ).distinct()


def build_schedule_rows(workers, days, shifts_by_day_worker):
    rows = []
    for worker in workers:
        cells = [
            {'date': day, 'shift': shifts_by_day_worker.get((worker.id, day))}
            for day in days
        ]
        rows.append({'worker': worker, 'cells': cells})
    return rows


def get_days_with_workers_count(days, shifts_by_day_worker, shop):
    days_info = []
    for day in days:
        count = sum(1 for (worker_id, shift_date), shift in shifts_by_day_worker.items() 
                   if shift_date == day and shift is not None and 
                   (shift.another_shop is None or shift.another_shop == shop))
        days_info.append({'date': day, 'workers_count': count})
    return days_info


def get_month_navigation(year, month):
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    return prev_year, prev_month, next_year, next_month


def schedule_view(request, slug, year=None, month=None):
    shop = get_object_or_404(CoffeeShop, slug=slug)
    today = timezone.now().date()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    days = get_month_days(year, month)
    workers = list(get_active_workers(shop, year, month))
    sync_workers_experience_years(workers)
    
    shifts = Shift.objects.filter(coffee_shop=shop, date__year=year, date__month=month)
    
    shifts_from_other_shops = Shift.objects.filter(
        another_shop=shop,
        date__year=year,
        date__month=month
    )
    
    all_shifts = list(shifts) + list(shifts_from_other_shops)
    shifts_by_day_worker = {(s.worker_id, s.date): s for s in all_shifts}
    
    workers_from_other_shops_ids = shifts_from_other_shops.values_list('worker_id', flat=True).distinct()
    workers_from_other_shops = list(Worker.objects.filter(id__in=workers_from_other_shops_ids))
    sync_workers_experience_years(workers_from_other_shops)
    
    all_workers = list(workers) + list(workers_from_other_shops)
    
    schedule_rows = build_schedule_rows(all_workers, days, shifts_by_day_worker)
    days_info = get_days_with_workers_count(days, shifts_by_day_worker, shop)
    prev_year, prev_month, next_year, next_month = get_month_navigation(year, month)

    return render(request, 'main/schedule/schedule.html', {
        'shop': shop,
        'days': days,
        'days_info': days_info,
        'workers': all_workers,
        'schedule_rows': schedule_rows,
        'min_workers': shop.minimum_workers,
        'year': year,
        'month': month,
        'all_shops': CoffeeShop.objects.all(),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    })


@require_POST
@csrf_protect
def update_shift(request):
    try:
        data = json.loads(request.body)
        worker = Worker.objects.get(id=data['worker_id'])
        target_shop = CoffeeShop.objects.get(id=data['coffee_shop_id'])
        day = datetime.strptime(data['date'], '%Y-%m-%d').date()
        value = (data.get('value') or '').strip()
    except (KeyError, json.JSONDecodeError, Worker.DoesNotExist, CoffeeShop.DoesNotExist, ValueError):
        return HttpResponseBadRequest('Invalid request')

    if worker.coffee_shop_id != target_shop.id:
        return HttpResponseForbidden('Нельзя менять график работника в чужой кофейне')

    if not value or value.lower() in ('выходной', 'off', 'none'):
        Shift.objects.filter(worker=worker, date=day).delete()
        return JsonResponse({'ok': True})

    defaults = {'coffee_shop': worker.coffee_shop, 'start_time': None, 'another_shop': None, 'is_plus': False}

    if value == '+':
        defaults['is_plus'] = True
    elif ':' in value:
        try:
            defaults['start_time'] = datetime.strptime(value, '%H:%M').time()
        except ValueError:
            return HttpResponseBadRequest('Invalid time')
    else:
        try:
            another_shop = CoffeeShop.objects.get(short_code=value)
            defaults['another_shop'] = another_shop
        except CoffeeShop.DoesNotExist:
            return HttpResponseBadRequest('Unknown value')

    Shift.objects.update_or_create(worker=worker, date=day, defaults=defaults)
    return JsonResponse({'ok': True})