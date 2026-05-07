from django.conf import settings
from django.core.management.commands.runserver import Command as RunserverCommand
from django.db import connection
from django.db.utils import OperationalError
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class Command(RunserverCommand):
    help = "Starts the Django development server with DB connectivity check."

    def inner_run(self, *args, **options):
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DB CHECK] Django metadata DB connected: engine={connection.vendor}, db={connection.settings_dict.get('NAME')}"
                )
            )
        except OperationalError as exc:
            self.stdout.write(self.style.ERROR(f"[DB CHECK] Django metadata DB failed: {exc}"))

        try:
            mongo = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
            mongo.admin.command("ping")
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DB CHECK] MongoDB connected: uri={settings.MONGODB_URI}, db={settings.MONGODB_DB_NAME}"
                )
            )
        except PyMongoError as exc:
            self.stdout.write(self.style.ERROR(f"[DB CHECK] MongoDB failed: {exc}"))

        return super().inner_run(*args, **options)
