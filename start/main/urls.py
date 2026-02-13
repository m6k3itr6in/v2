from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('shops/<slug:slug>/', views.get_workers, name='workers'),
    path('workers/<int:worker_id>/', views.worker_detail, name='worker_detail'),
    path('schedule/<slug:slug>/<int:year>/<int:month>/', views.schedule_view, name='schedule'),
    path('api/schedule/update/', views.update_shift, name='update_shift'),
    path('shift/offer/', views.offer_shift_exchange, name='offer_shift_exchange'),
    path('applications/confirm/', views.confirm_take_shift, name='confirm_take_shift'),
    path('applications/', views.shift_applications, name='shift_applications'),
    path('applications/accept/', views.accept_application, name='accept_application'),
    path('applications/reject/', views.reject_application, name='reject_application'),
    path('workers/add/', views.add_worker, name='add_worker'),
    path('workers/register_vacation/<int:worker_id>/', views.register_vacation, name='register_vacation'),
    path('managment/assign/', views.assign_shop_admin, name='assign_shop_admin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.log_out, name='logout'),
    path('statistics/', views.statistics, name='statistics'),
]