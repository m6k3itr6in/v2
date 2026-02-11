from django import forms
from django.contrib.auth.models import User
from .models import Worker, CoffeeShop, ShopAdmin, UserProfile

class WorkerCreationForm(forms.ModelForm):
    username = forms.CharField(label='Login', max_length=150)
    password = forms.CharField(label='Pass', widget=forms.PasswordInput)

    class Meta:
        model = Worker
        fields = ['name', 'phone_number', 'start_date_experience_years']
        widgets = {
            'start_date_experience_years':forms.DateInput(attrs={'type':'date'}),
        }

    def save(self, commit=True, shop=None):
        worker = super().save(commit=False)

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )

        worker.user = user
        if shop:
            worker.coffee_shop = shop
        
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