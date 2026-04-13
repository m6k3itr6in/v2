from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Worker, CoffeeShop, ShopAdmin, UserProfile

phone_validator = RegexValidator(
    regex=r'^(\+7|7|8)[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
    message="Введите корректный номер телефона."
)
from django.conf import settings
from .utils import send_push_to_admin

class WorkerSelfRegistrationForm(forms.Form):
    username = forms.CharField(
        label='Логин', 
        max_length=50, 
        widget=forms.TextInput(attrs={'placeholder': 'Логин', 'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='Имя', 
        max_length=50, 
        widget=forms.TextInput(attrs={'placeholder': 'Имя', 'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Фамилия', 
        max_length=50, 
        widget=forms.TextInput(attrs={'placeholder': 'Фамилия', 'class': 'form-control'})
    )
    phone_number = forms.CharField(
        label='Телефон', 
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '89000000000', 'type': 'tel', 'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль', 
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите пароль', 'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        label='Повторите пароль', 
        widget=forms.PasswordInput(attrs={'placeholder': 'Подтвердите пароль', 'class': 'form-control'})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        digits = ''.join(filter(str.isdigit, phone))
        
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            pass
        elif len(digits) == 10:
            digits = '7' + digits
            
        return f'+{digits}'

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
            name=self.cleaned_data['first_name'] + ' ' + self.cleaned_data['last_name'],
            phone_number=self.cleaned_data['phone_number'],
            coffee_shop=None,
            start_date_experience_years=None,
        )

        send_push_to_admin(
            title="Новая регистрация!",
            body=f"Зарегестрировался {worker.name}. Требуется подтверждение.",
            url=f"{settings.SITE_URL}/managment/pending/"
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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя и фамилия'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '89000000000', 'type': 'tel', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].validators.append(phone_validator)

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        digits = ''.join(filter(str.isdigit, phone))
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        return f'+{digits}'

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
    user = forms.ModelChoiceField(
        queryset=User.objects.all(), 
        label='Пользователь',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ShopAdmin
        fields = ['user', 'coffee_shop']
        labels = {
            'coffee_shop': 'Кофейня',
        }
        widgets = {
            'coffee_shop': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        shop_admin = super().save(commit=False)
        if commit:
            shop_admin.save()
            profile, _ = UserProfile.objects.get_or_create(user=shop_admin.user)
            profile.role = 'SHOP_ADMIN'
            profile.save()
        
        return shop_admin



# from django import forms
# from django.core.validators import RegexValidator

# phone_validator = RegexValidator(
#     regex=r'^(\+7|7|8)[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
#     message="Неверный формат номера. Используйте стандарт 8XXXXXXXXXX или +7XXXXXXXXXX."
# )

# class WorkerSelfRegistrationForm(forms.Form):
#     phone_number = forms.CharField(
#         label='Телефон', 
#         validators=[phone_validator],
#         widget=forms.TextInput(attrs={'class': 'form-control'})
#     )