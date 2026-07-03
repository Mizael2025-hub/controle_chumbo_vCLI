import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Aguarda o banco de dados ficar disponível (usado no entrypoint Docker)."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=90)

    def handle(self, *args, **options):
        timeout = options["timeout"]
        self.stdout.write("==> Waiting for database...")
        conn = connections["default"]
        for i in range(timeout):
            try:
                conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS("Database ready."))
                return
            except OperationalError:
                if i == 0:
                    self.stdout.write("DB not ready; retrying...")
                time.sleep(1)
        self.stderr.write(self.style.ERROR("Database not available."))
        raise SystemExit(1)
