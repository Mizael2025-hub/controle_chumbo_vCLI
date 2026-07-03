from dataclasses import dataclass, field
from typing import List

from django.db import models


class ModuleRole(models.TextChoices):
    ADMIN = "admin", "Administrador"
    OPERADOR = "operador", "Operador"


@dataclass
class MenuItem:
    label: str
    url_name: str
    admin_only: bool = False


@dataclass
class ModuleManifest:
    slug: str
    label: str
    icon: str
    order: int = 10
    url_name: str = ""
    roles: List[str] = field(default_factory=list)
    menu: List[MenuItem] = field(default_factory=list)
    dashboard_widgets: List[str] = field(default_factory=list)

    def menu_for(self, user) -> List[MenuItem]:
        """Itens de menu visíveis ao usuário."""
        is_admin = user.is_superuser or getattr(user, "role", None) == "admin"
        out = []
        for item in self.menu:
            if item.admin_only and not is_admin:
                continue
            out.append(item)
        return out
