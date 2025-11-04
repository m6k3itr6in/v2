from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('worker/<int:id>/', views.get_workers, name='workers'),
    path('schedule/<int:coffee_shop_id>/<int:year>/<int:month>/', views.schedule_view, name='schedule'),
    path('api/schedule/update/', views.update_shift, name='update_shift'),
]
