from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('shops/<slug:slug>/', views.get_workers, name='workers'),
    path('workers/<int:worker_id>/', views.worker_detail, name='worker_detail'),
    path('schedule/<slug:slug>/<int:year>/<int:month>/', views.schedule_view, name='schedule'),
    path('api/schedule/update/', views.update_shift, name='update_shift'),
    path('shift/offer/<int:shift_id>/', views.offer_shift_exchange, name='offer_shift_exchange'),
    path('shift/take/<int:request_id>/', views.take_shift, name='take_shift'),
    path('shift/approve/<int:request_id>/', views.approve_shift_request, name='approve_shift_request'),
    path('workers/add/', views.add_worker, name='add_worker'),
    path('managment/assign/', views.assign_shop_admin, name='assign_shop_admin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.log_out, name='logout'),
]