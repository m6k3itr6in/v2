from django.core.management.base import BaseCommand
from main.utils import check_and_notify_understaffing

class Command(BaseCommand):
    help = 'Проверяет график на нехватку персонала за 2 дня до даты и отправляет пуш-уведомления админам.'

    def handle(self, *args, **options):
        self.stdout.write('Запуск проверки персонала...')
        check_and_notify_understaffing()
        self.stdout.write(self.style.SUCCESS('Проверка завершена успешно.'))
