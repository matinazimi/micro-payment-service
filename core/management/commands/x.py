from django.core.management.base import BaseCommand

from core.service.dummy import dummyFunction


class Command(BaseCommand):

    def handle(self, *args, **options):
        dummyFunction("This is the test 1", "This is the test 2")
        print("SUCCESS")
