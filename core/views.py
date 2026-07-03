from pathlib import Path

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache

_ROOT = Path(__file__).resolve().parent.parent


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@never_cache
def manifest_json(request: HttpRequest) -> HttpResponse:
    f = _ROOT / "manifest.json"
    if not f.exists():
        return HttpResponse(status=404)
    return HttpResponse(
        f.read_text(encoding="utf-8"), content_type="application/manifest+json"
    )


@never_cache
def service_worker(request: HttpRequest) -> HttpResponse:
    f = _ROOT / "sw.js"
    if not f.exists():
        return HttpResponse(status=404)
    resp = HttpResponse(
        f.read_text(encoding="utf-8"), content_type="application/javascript"
    )
    resp["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp["Service-Worker-Allowed"] = "/"
    return resp
