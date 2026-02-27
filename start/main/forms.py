from django import forms
from django.contrib.auth.models import User
from .models import Worker, CoffeeShop, ShopAdmin, UserProfile

class WorkerSelfRegistrationForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)
    name = forms.CharField(label='Имя и фамилия', max_length=50)
    phone_number = forms.CharField(label='Телефон', max_length=15)

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Пароли не совпадают')
        username = cleaned.get('username')
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', 'Такой логин уже занят')
        return cleaned

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
        )

        worker = Worker(
            user=user,
            name=self.cleaned_data['name'],
            phone_number=self.cleaned_data['phone_number'],
            coffee_shop=None,
            start_date_experience_years=None,
        )

        if commit:
            worker.save()
            UserProfile.objects.create(user=user, role='WORKER')
        return worker

class WorkerCreationForm(forms.ModelForm):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    class Meta:
        model = Worker
        fields = ['name', 'phone_number']

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Пароли не совпадают')
        return cleaned

    def save(self, commit=True, shop=None):
        worker = super().save(commit=False)

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
        )

        worker.coffee_shop = shop if shop else None
        
        if commit:
            worker.save()
            UserProfile.objects.create(user=user, role='WORKER')
        
        return worker

class AssignmentForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label='User')

    class Meta:
        model = ShopAdmin
        fields = ['user', 'coffee_shop']

    def save(self, commit=True):
        shop_admin = super().save(commit=False)
        if commit:
            shop_admin.save()
            profile, _ = UserProfile.objects.get_or_create(user=shop_admin.user)
            profile.role = 'SHOP_ADMIN'
            profile.save()
        
        return shop_admin