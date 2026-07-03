from modules.chumbo._crud import make
from .forms import DestinoForm
from .models import Destino

DestinoList, DestinoCreate, DestinoUpdate, DestinoDelete = make(
    Destino, DestinoForm, "destinos", "Destinos de saída", ["nome", "slug", "sort_order"]
)
