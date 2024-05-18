from django.core.management.base import BaseCommand
from telegrambot.main import RunBot

class Command(BaseCommand):
    help = 'Run bot'

    def handle(self, *args, **options):
        RunBot()