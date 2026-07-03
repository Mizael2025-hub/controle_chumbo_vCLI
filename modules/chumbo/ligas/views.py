from modules.chumbo._crud import make
from .forms import LigaForm
from .models import Liga

LigaList, LigaCreate, LigaUpdate, LigaDelete = make(
    Liga, LigaForm, "ligas", "Ligas", ["nome", "chave_cor", "sort_order"]
)
