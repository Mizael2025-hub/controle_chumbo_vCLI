import time

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect


class SessionTimeoutMiddleware:
    """RF03: timeout de sessão por inatividade (SESSION_COOKIE_AGE)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_COOKIE_AGE", 1800)

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()
            last = request.session.get("last_activity", now)
            if now - last > self.timeout:
                logout(request)
                return redirect(settings.LOGIN_URL)
            request.session["last_activity"] = now
        return self.get_response(request)


class ModuleContextMiddleware:
    """Injeta `request.module` (slug) a partir do namespace da URL resolvida."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.module = None
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.module = None
        match = getattr(request, "resolver_match", None)
        if not match:
            return None
        ns = (match.namespace or "").split(":")
        top = ns[0] if ns else ""
        if not top:
            return None
        try:
            from modules.registry import slugs
        except Exception:
            return None
        if top in slugs():
            request.module = top
        return None
