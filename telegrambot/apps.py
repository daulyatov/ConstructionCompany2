from django.apps import AppConfig


class TelegrambotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegrambot'

    def ready(self):
        import telegrambot.signals
