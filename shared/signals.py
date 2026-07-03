from django.dispatch import Signal

# Eventos de domínio publicáveis (§2.3). Módulos podem ouvir para reagir.
setor_criado = Signal()
setor_atualizado = Signal()
operador_criado = Signal()
turno_criado = Signal()
maquina_criada = Signal()
