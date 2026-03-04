from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from . import scheduler
            scheduler.start()
