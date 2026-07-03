from modules.chumbo._crud import make
from .forms import ModeloForm
from .models import ModeloProduto

ModeloList, ModeloCreate, ModeloUpdate, ModeloDelete = make(
    ModeloProduto,
    ModeloForm,
    "modelos",
    "Modelos de produto",
    ["nome", "polaridade", "placas_por_grade"],
)
