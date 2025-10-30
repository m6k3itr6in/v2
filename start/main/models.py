from django.db import models

# Create your models here.
class CoffeeShop(models.Model):
    name = models.CharField(max_length=50)
    short_code = models.CharField(max_length=10, unique=True, default='')
    minimum_workers = models.IntegerField(default=4)

    def __str__(self):
        return self.name
    

class Worker(models.Model):
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    experience_years = models.IntegerField()
    start_date_experience_years = models.DateField()
    hourly_rate = models.IntegerField()
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE, related_name='workers')
    fired_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Shift(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    coffee_shop = models.ForeignKey(CoffeeShop, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    another_shop = models.ForeignKey(CoffeeShop, null=True, blank=True, on_delete=models.SET_NULL, related_name='extra_shift')