from django.shortcuts import render, redirect, get_object_or_404
from .models import CoffeeShop, Worker, Shift, UserProfile, ShopAdmin, ShiftRequest
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
import calendar
from datetime import date, timedelta, datetime
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect
from functools import wraps
from .forms import WorkerCreationForm, AssignmentForm

def get_user_profile(user):
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'SUPER_ADMIN'
    
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user, role='WORKER')
        return 'WORKER'

def sync_workers_experience_years(workers):
    today = timezone.localdate()
    to_update = []
    for w in workers:
        if w.sync_experience_years(as_of=today, save=False):
            to_update.append(w)
    if to_update:
        Worker.objects.bulk_update(to_update, ["experience_years"])

def index(request):
    role = get_user_role(request.user)

    if role == 'SUPER_ADMIN':
        cafes = CoffeeShop.objects.all()
        return render(request, 'main/index/super_admin_index.html', {'cafes':cafes})
    
    if role == 'SHOP_ADMIN':
        admin_shops = ShopAdmin.objects.filter(user=request.user).values_list('coffee_shop_id', flat=True)
        cafes = CoffeeShop.objects.filter(id__in=admin_shops)
        return render(request, 'main/index/index.html', {'cafes':cafes})

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
    role = get_user_role(request.user)
    return render(request, 'main/workers/worker.html', {'worker': worker, 'role': role})

def get_month_days(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, d) for d in range(1, num_days + 1)]

def get_active_workers(shop, year, month):
    month_start = date(year, month, 1)
    return Worker.objects.filter(coffee_shop=shop).filter(Q(fired_at__isnull=True) | Q(fired_at__gt=month_start)).distinct()

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
    role = get_user_role(request.user)

    if role == 'SHOP_ADMIN':
        is_assigned = ShopAdmin.objects.filter(user=request.user, coffee_shop=shop).exists()
        if not is_assigned:
            return HttpResponseForbidden("Your not admin on this shop")

    today = timezone.now().date()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    days = get_month_days(year, month)
    workers = list(get_active_workers(shop, year, month))
    sync_workers_experience_years(workers)
    
    shifts = Shift.objects.filter(coffee_shop=shop, date__year=year, date__month=month)
    
    shifts_from_other_shops = Shift.objects.filter(another_shop=shop, date__year=year, date__month=month)
    
    all_shifts = list(shifts) + list(shifts_from_other_shops)
    shifts_by_day_worker = {(s.worker_id, s.date): s for s in all_shifts}
    
    workers_from_other_shops_ids = shifts_from_other_shops.values_list('worker_id', flat=True).distinct()
    workers_from_other_shops = list(Worker.objects.filter(id__in=workers_from_other_shops_ids))
    sync_workers_experience_years(workers_from_other_shops)
    
    all_workers = list(workers) + list(workers_from_other_shops)
    
    schedule_rows = build_schedule_rows(all_workers, days, shifts_by_day_worker)
    days_info = get_days_with_workers_count(days, shifts_by_day_worker, shop)
    prev_year, prev_month, next_year, next_month = get_month_navigation(year, month)

    active_requests = ShiftRequest.objects.filter(shift__coffee_shop=shop, shift__date__year=year, shift__date__month=month, status='PENDING').select_related('shift', 'worker', 'taken_by')

    requests_map = {(r.shift.worker_id, r.shift.date) for r in active_requests}

    my_future_shifts = []
    if role == 'WORKER':
        worker = getattr(request.user, 'worker_profile', None)
        if worker:
            my_future_shifts = Shift.objects.filter(
                worker=worker,
                date__gte=timezone.now().date(),
                coffee_shop=shop
            ).order_by('date')

    return render(request, 'main/schedule/schedule.html', {
        'shop': shop,
        'role': role,
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
        'requests_map':requests_map,
        'my_future_shifts':my_future_shifts,
    })

@login_required
@require_POST
def offer_shift_exchange(request):
    shift_id = request.POST.get('shift_id')
    shift = get_object_or_404(Shift, id=int(shift_id))
    worker = getattr(request.user, 'worker_profile', None)
    if not worker or shift.worker != worker:
        return HttpResponseForbidden('Не ваша смена')

    if ShiftRequest.objects.filter(shift=shift, status='PENDING').exists():
        messages.warning(request, 'Заявка уже есть')
    else:
        ShiftRequest.objects.create(shift=shift, worker=worker, reason=request.POST.get('reason', ''), status='PENDING')
        messages.success(request, 'Смена выставлена')
    
    return redirect('main:schedule', slug=shift.coffee_shop.slug, year=shift.date.year, month=shift.date.month)

@login_required
@require_POST
def take_shift(request, request_id):
    shift_req = get_object_or_404(ShiftRequest, id=request_id, status='PENDING')
    worker = getattr(request.user, 'worker_profile', None)
    if not worker:
        return HttpResponseForbidden('No worker profile')
    
    if shift_req.worker == worker:
        return HttpResponseBadRequest("Нельзя забрать свою же смену.")
    
    shift_req.taken_by = worker
    shift_req.taken_at = timezone.now()
    shift_req.save()
    
    messages.info(request, "Ваш запрос на взятие смены отправлен на подтверждение админу.")
    return redirect('main:schedule', slug=shift_req.shift.coffee_shop.slug, year=shift_req.shift.date.year, month=shift_req.shift.date.month)

@login_required
def approve_shift_request(request, request_id):
    role = get_user_role(request.user)
    if role not in ['SHOP_ADMIN', 'SUPER_ADMIN']:
        return HttpResponseForbidden("Нет прав")
    
    shift_req = get_object_or_404(ShiftRequest, id=request_id, status='PENDING')

    if not shift_req.taken_by:
        messages.error(request, "Никто еще не вызвался забрать эту смену.")
        return redirect(request.META.get('HTTP_REFERER'))

    shift = shift_req.shift
    shift.worker = shift_req.taken_by
    shift.save()

    shift_req.status = 'APPROVED'
    shift_req.approved_by = request.user
    shift_req.approved_at = timezone.now()
    shift_req.save()

    messages.success(request, f"Смена успешно передана сотруднику {shift.worker.name}")
    return redirect('main:schedule', slug=shift.coffee_shop.slug, year=shift.date.year, month=shift.date.month)

@require_POST
@csrf_protect
def update_shift(request):
    role = get_user_role(request.user)
    if role != 'SHOP_ADMIN':
        return HttpResponseForbidden("You are not admin")

    if role == 'SUPER_ADMIN':
        return HttpResponseForbidden("Youre super admin")

    try:
        data = json.loads(request.body)
        worker = Worker.objects.get(id=data['worker_id'])
        target_shop = CoffeeShop.objects.get(id=data['coffee_shop_id'])
        day = datetime.strptime(data['date'], '%Y-%m-%d').date()
        value = (data.get('value') or '').strip()

        if not ShopAdmin.objects.filter(user=request.user, coffee_shop=target_shop).exists():
            return HttpResponseForbidden("Вы не админ этой конкретной кофейни")
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

@login_required
def add_worker(request):
    role = get_user_role(request.user)
    if role != 'SHOP_ADMIN' and role != 'SUPER_ADMIN':
        return HttpResponseForbidden("Вы не админ")

    admin_relation = ShopAdmin.objects.filter(user=request.user).first()

    if not admin_relation:
        return HttpResponseForbidden("Нет привязанной кофейни")

    shop = admin_relation.coffee_shop

    if request.method == 'POST':
        form = WorkerCreationForm(request.POST)
        if form.is_valid():
            form.save(shop=shop)

            messages.success(request, 'Сотрудник добавлен')
            return redirect('main:schedule', slug=shop.slug, year=timezone.now().year, month=timezone.now().month)
    else:
        form = WorkerCreationForm()

    return render(request, 'main/workers/add_worker.html', {'form':form, 'shop':shop})


@login_required
def assign_shop_admin(request):
    role = get_user_role(request.user)

    if role != 'SUPER_ADMIN':
        return HttpResponseForbidden("Вы не админ")

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Админ назначен')
            return redirect('main:index')
    else:
        form = AssignmentForm()

    return render(request, 'main/admin/assign_admin.html', {'form':form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('main:index')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'main/auth/login.html')

def log_out(request):
    logout(request)
    return redirect('main:login')

@login_required
@require_POST
def register_vacation(request, worker_id):
    role = get_user_role(request.user)
    if role == 'WORKER':
        return HttpResponseForbidden("Вы не админ")

    worker = get_object_or_404(Worker, id=worker_id)
    
    if role == 'SHOP_ADMIN':
        admin_shop = ShopAdmin.objects.filter(user=request.user).first()
        if not admin_shop or admin_shop.coffee_shop != worker.coffee_shop:
            return HttpResponseForbidden("Вы не админ этой конкретной кофейни")
    else:
        pass

    worker.vacation = timezone.now().date()
    worker.save()
    
    return redirect('main:worker_detail', worker.id)