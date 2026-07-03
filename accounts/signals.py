from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Role, User


@receiver(post_save, sender=User)
def ensure_admin_role(sender, instance, **kwargs):
    """Superuser é sempre admin global (cosmético; is_admin já cobre o acesso)."""
    if instance.is_superuser and instance.role != Role.ADMIN:
        User.objects.filter(pk=instance.pk).update(role=Role.ADMIN)
