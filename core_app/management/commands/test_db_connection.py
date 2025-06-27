# C:\entc\core_app\management\commands\test_db_connection.py

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import time

class Command(BaseCommand):
    help = 'Tests database connection by attempting to connect and print status.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Attempting to connect to database..."))
        db_conn = connections['default']
        try:
            db_conn.cursor()
            self.stdout.write(self.style.SUCCESS("Successfully connected to the database!"))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f"Failed to connect to database: {e}"))
            self.stdout.write(self.style.ERROR("Retrying connection in 5 seconds..."))
            time.sleep(5) # Wait and retry once
            try:
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS("Successfully reconnected to the database on retry!"))
            except OperationalError as retry_e:
                self.stdout.write(self.style.ERROR(f"Failed to connect to database after retry: {retry_e}"))
                raise # Re-raise the error to make the deploy fail loudly
