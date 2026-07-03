import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import Role
from accounts.module_perms import ModulePermission
from modules.chumbo.destinos.models import Destino
from modules.chumbo.ligas.models import CorChave, Liga
from modules.chumbo.modelos.models import ModeloProduto, Polaridade
from shared.services import seed_shared


def seed_chumbo():
    destinos = ["VRLA", "Óxido", "Venda", "Teleiras", "Exportação"]
    for i, nome in enumerate(destinos):
        Destino.objects.get_or_create(nome=nome, defaults={"sort_order": i})

    ligas = [
        ("Liga Azul", CorChave.AZUL),
        ("Liga Amarela", CorChave.AMARELO),
        ("Liga Vermelha", CorChave.VERMELHO),
    ]
    for i, (nome, cor) in enumerate(ligas):
        Liga.objects.get_or_create(nome=nome, defaults={"chave_cor": cor, "sort_order": i})

    modelos = [
        ("Modelo A12", Polaridade.POSITIVA, 12),
        ("Modelo B9", Polaridade.NEGATIVA, 9),
    ]
    for i, (nome, pol, placas) in enumerate(modelos):
        ModeloProduto.objects.get_or_create(nome=nome, defaults={"polaridade": pol, "placas_por_grade": placas, "sort_order": i})

    return {
        "destinos": Destino.objects.count(),
        "ligas": Liga.objects.count(),
        "modelos": ModeloProduto.objects.count(),
    }


class Command(BaseCommand):
    help = "Popula dados de demonstração (Faker pt_BR)."

    def handle(self, *args, **options):
        Faker("pt_BR")
        User = get_user_model()

        admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@komotores.local")
        admin_pass = os.environ.get("SEED_ADMIN_PASSWORD", "admin123456")
        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "name": "Administrador",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password(admin_pass)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Admin criado: {admin_email} / {admin_pass}"))
        else:
            self.stdout.write(f"Admin já existe: {admin_email}")

        op, created = User.objects.get_or_create(
            email="operador@komotores.local",
            defaults={"name": "Operador Demo", "role": Role.OPERATOR},
        )
        if created:
            op.set_password("operador123456")
            op.save()
            self.stdout.write(self.style.SUCCESS("Operador criado: operador@komotores.local / operador123456"))

        # Permissão do operador no módulo Chumbo (RBAC por módulo §2.6).
        ModulePermission.objects.get_or_create(
            user=op,
            module_slug="chumbo",
            defaults={"role": "operador"},
        )
        self.stdout.write("Permissao operador->chumbo(operador) garantida.")

        counts_shared = seed_shared()
        self.stdout.write(self.style.SUCCESS(f"Seed shared OK: {counts_shared}"))

        counts_chumbo = seed_chumbo()
        self.stdout.write(self.style.SUCCESS(f"Seed chumbo OK: {counts_chumbo}"))
