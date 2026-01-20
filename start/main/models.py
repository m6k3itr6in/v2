from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import re

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
class CoffeeShop(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    short_code = models.CharField(max_length=10, unique=True, default='')
    minimum_workers = models.IntegerField(default=4)

    def save(self, *args, **kwargs):
        if not self.slug:
            transliterated = transliterate(self.name)
            self.slug = slugify(transliterated)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Worker(models.Model):
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    experience_years = models.IntegerField(default=0)
    start_date_experience_years = models.DateField()
    hourly_rate = models.IntegerField()
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='workers')
    fired_at = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='workers/photos/', null=True, blank=True)

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
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    another_shop = models.ForeignKey(CoffeeShop, null=True, blank=True, on_delete=models.SET_NULL, related_name='extra_shift')
    is_plus = models.BooleanField(default=False)