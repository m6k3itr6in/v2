from django.db import models
from encrypted_model_fields.fields import EncryptedCharField
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

def transliterate(text):
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    result = ''
    for char in text:
        result += translit_map.get(char, char)
    return result

# Create your models here.
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Супер-админ'),
        ('SHOP_ADMIN', 'Админ точки'),
        ('WORKER', 'Работник')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='WORKER')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_profiles'
        indexes = [models.Index(fields=['role'])]
    
    def __str__(self):
        return self.user.username

class CoffeeShop(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    short_code = models.CharField(max_length=10, unique=True, default='')
    minimum_workers = models.IntegerField(default=4)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(transliterate(self.name))
        if not self.short_code:
            self.short_code = transliterate(self.name)[:3].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ShopAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_shops')
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='admins')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'coffee_shop']
        db_table = 'shop_admins'
        indexes = [models.Index(fields=['user', 'coffee_shop'])]

    def __str__(self):
        return self.user.username

class Worker(models.Model):
    name = models.CharField(max_length=50)
    phone_number = EncryptedCharField(max_length=15)
    experience_years = models.IntegerField(default=0)
    start_date_experience_years = models.DateField()
    hourly_rate = models.IntegerField()
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='workers')
    fired_at = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='workers/photos/', null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='worker_profile')
    vacation = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'workers'
        indexes = [models.Index(fields=['coffee_shop', 'fired_at']), models.Index(fields=['user'])]

    def get_vacation_start_date(self):
        if self.vacation:
            return self.vacation + datetime.timedelta(days=180)

        if self.start_date_experience_years:
            return self.start_date_experience_years + datetime.timedelta(days=180)

    def compute_experience_years(self, as_of=None) -> int:
        if not self.start_date_experience_years:
            return 0
        as_of = as_of or timezone.localdate()
        start = self.start_date_experience_years
        years = as_of.year - start.year
        if (as_of.month, as_of.day) < (start.month, start.day):
            years -= 1
        return max(0, years)

    def sync_experience_years(self, as_of=None, save=False) -> bool:
        new_val = self.compute_experience_years(as_of=as_of)
        if self.experience_years == new_val:
            return False
        self.experience_years = new_val
        if save:
            self.save(update_fields=["experience_years"])
        return True

    def __str__(self):
        return self.name
    
class Shift(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='shifts')
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    another_shop = models.ForeignKey(CoffeeShop, null=True, blank=True, on_delete=models.SET_NULL, related_name='extra_shift')
    is_plus = models.BooleanField(default=False)
    replacement_worker = models.ForeignKey(Worker, null=True, blank=True, on_delete=models.SET_NULL, related_name='replacement_shifts')

    class Meta:
        unique_together = ['worker', 'date']
        db_table = 'shifts'
        indexes = [models.Index(fields=['coffee_shop', 'date']), models.Index(fields=['worker', 'date']), models.Index(fields=['date'])]

    def __str__(self):
        return self.worker.name


class ShiftRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает подтверждения'),
        ('APPROVED', 'Подтверждено'),
        ('REJECTED', 'Отклонено'),
        ('TAKEN', 'Взято другим работником'),
        ('CANCELED', 'Отменено')
    ]

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='requests')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='shift_requests')
    reason = models.TextField(verbose_name='Причина отдачи смены', max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_shift_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    taken_by = models.ForeignKey(Worker, null=True, blank=True, on_delete=models.SET_NULL, 
                                 related_name='taken_shifts')
    taken_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'shift_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', 'requested_at']),
            models.Index(fields=['shift', 'status']),
            models.Index(fields=['worker', 'status']),
        ]
    
    def __str__(self):
        return self.worker.name