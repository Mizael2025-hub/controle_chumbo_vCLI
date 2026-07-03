# PRD — Plataforma PCP (Módulo: Controle de Chumbo)

> **Product Requirements Document**
> Refatorado: o repositório agora é a **Plataforma PCP da fábrica** (chão de fábrica digital) e o **Controle de Chumbo** é o primeiro **módulo** instalado sobre ela. Módulos futuros (Óxido, Borra, Qualidade, Manutenção...) são adicionados sem alterar a plataforma (ver §2.0).
> Stack: Python + Django + LangChain + PostgreSQL · Metodologia: Workflow de IA Assistida (PycodeBR) — Spec-Driven Development.

---

## 1. Visão Geral

### 1.1 Propósito

**Plataforma PCP** (Produção/Planejamento e Controle) para indústria de baterias: um chão de fábrica digital modular, onde cada **módulo** cobre um controle/setor. O **módulo Controle de Chumbo** (primeiro) substitui o controle manual em papel/PDF por um sistema que rastreia todo o ciclo de vida do chumbo — da chegada dos lingotes (lotes) ao consumo na produção. Módulos seguintes ampliam a plataforma para outros setores/controles sem reescrevê-la.

### 1.2 Problema Resolvido

O chumbo chega em lingotes organizados em lotes, que são empilhados em montes dispostos numa grade 2D no chão da fábrica, separados por liga. O controle manual gera:
- Erros de cálculo de saldo
- Perda de rastreabilidade (who/what/when)
- Dificuldade de auditoria
- Retrabalho em inventário físico
- Sem visibilidade em tempo real do estoque disponível

O sistema resolve tudo isso com um **espelho digital do chão de fábrica**.

### 1.3 Stack (definida)

| Camada | Tecnologia | Versão mínima |
|--------|-----------|---------------|
| Linguagem | Python | 3.13+ |
| Framework Web | Django | 5.x (ou 6.x quando estável) |
| ORM / BD | PostgreSQL + Django ORM | Postgres 16+ |
| Driver DB | `psycopg[binary]` | 3.2+ |
| IA (orquestração) | LangChain + LangGraph | 1.0+ |
| Tarefas assíncronas | Celery + RabbitMQ | Celery 5.4+, RabbitMQ 3.13+ |
| Agendamento / Result Celery | `django-celery-beat` + `django-celery-results` | — |
| Painel de tasks no Admin | `dj-celery-panel` | — |
| Cache / result backend | Redis | 7+ |
| Staticfiles em prod | WhiteNoise (compresso) | — |
| Settings/env | `django-environ` | — |
| WSGI | Gunicorn (gthread, 2 threads) | 22+ |
| Dev Containers | Docker Compose | — |
| Produção | Docker Swarm | — |
| Proxy / SSL | Traefik (Let's Encrypt via Cloudflare DNS-01) | 3.0+ |
| DNS / CDN | Cloudflare | — |
| Registro de Imagens | GHCR (GitHub Container Registry) | — |
| PWA / Offline | Service Worker (Workbox) + IndexedDB (Outbox) + Background Sync | — |
| Frontend | Django Templates + HTMX + Alpine.js + Design System extraído | — |
| PDF (relatórios) | Reportlab | — |

### 1.4 CLIs de IA para assistência

- OpenCode (conectado a múltiplos provedores)
- Claude Code (Anthropic — Opus 4.8)
- Codex CLI (OpenAI — GPT-5.5)

### 1.5 Modelos de IA recomendados

- GLM-5.2, MiniMax M3, Kimi K2.7 Code (OpenCode Go)
- GPT-5.5 (ChatGPT Plus)
- Opus 4.8 (Claude Code Max)
- DeepSeek V4 Flash / Pro (alto limite de contexto)

---

## 2. Arquitetura do Sistema

### 2.0 Conceito: Plataforma + Módulos

> Este repositório **NÃO é "o sistema de chumbo"** — é a **Plataforma PCP da fábrica** (chão de fábrica digital). O **Controle de Chumbo** é apenas o **primeiro módulo** instalado sobre essa plataforma. Módulos futuros (Controle de Óxido, Controle de Borra, Qualidade, Manutenção, etc.) são adicionados **sem alterar a plataforma**.

A arquitetura separa três camadas com **responsabilidades distintas**:

| Camada | O que é | Apps | Pode importar |
|--------|---------|-----|---------------|
| **Plataforma** | Infraestrutura fixa, compartilhada por todos os módulos | `core`, `base`, `accounts`, `shell`, `shared` | só a si mesma |
| **Módulos** | Domínio de negócio, **opcional e descartável** | `modules/<nome>/` | Plataforma + `shared` + o próprio módulo (**nunca outro módulo**) |
| **(futuro) Integrações** | Pontes externas (ERP, SPC, etc.) | `integrations/` | Plataforma + `shared` |

**Regra de ouro da modularidade:** um módulo **nunca** importa diretamente outro módulo (`from modules.oxido...` dentro de `modules.chumbo`). Comunicação entre módulos, quando necessária, ocorre por:
1. **Dados compartilhados** via `shared/` (ex.: Setor, Operador, Turno — que vários módulos usam).
2. **Consultas aos mesmos modelos `shared`** (cada módulo lê o que precisa; nenhum "chama" o outro).
3. **Eventos de domínio** via signals do Django em `shared/` (ex.: signal `setor_criado` que um módulo novo pode ouvir) — **se e quando** houver acoplamento real.

### 2.1 Visão de Alto Nível

```
Usuário (Celular principal / Tablet / Desktop)
    │
    ▼
[Navegador / PWA instalável] ← Shell (layout + nav dinâmica + dashboard agregado)
    │
    ▼
[Plataforma: Django + HTMX/Alpine] ── [accounts: auth + RBAC por módulo]
    │
    ├──► [Módulo Chumbo]   /chumbo/    (lotes, montes, grade, consumo, relatórios)
    ├──► [Módulo Futuro X] /x/         (...)
    └──► [Módulo Futuro Y] /y/         (...)
    │
    ├──► PostgreSQL       (shared masters + dados de cada módulo)
    ├──► Celery + RabbitMQ (tarefas assíncronas de qualquer módulo)
    └──► LangChain/Graph  (agentes IA por módulo / assistente geral)
```

### 2.2 Padrão Arquitetural

**Monolito modular** (Django clássico) com **apps na raiz** (sem pasta `apps/`), organizado em **Plataforma** + **namespace `modules/`**. Princípios:

- **Plataforma primeiro:** `core` (config), `base` (infra: `BaseModel`, mixins, registry), `accounts` (auth + RBAC), `shell` (layout + nav + dashboard agregado), `shared` (cadastros cross-módulo) — fixos, estáveis, sem conter regras de negócio.
- **Módulos isolados** em `modules/<nome>/`: cada módulo é um **pacote Python** contendo suas próprias sub-apps Django (ex.: `modules/chumbo/lotes`, `modules/chumbo/montes`). Um módulo pode ser **removido** apagando a pasta + retirando do `INSTALLED_APPS`/registry — nada da plataforma quebra.
- **Manifest declarativo:** cada módulo expõe `modules/<nome>/manifest.py` com metadados (slug, label, ícone, item de menu, permissões exigidas, widgets de dashboard). O `shell` lê o **registry** (montado no `AppConfig.ready()`) e constrói nav/menu **dinamicamente** — adicionar/remover módulo não mexe no `shell`.
- **Thin views, fat services:** lógica de domínio em `services.py`; views (CBV) só orquestram.
- **HTMX** para interações dinâmicas sem SPA; **Alpine.js** para estado local (grade 2D, popovers).
- **Celery** para tarefas pesadas (relatórios, consumo em lote); **LangChain/LangGraph** para agentes IA por módulo.
- **Signals** em `signals.py` das apps/conector, ligados no `AppConfig.ready()` (nunca em `models.py`).
- **Custom `User`** fixado **antes do primeiro migrate** (`AUTH_USER_MODEL`).
- **Código em inglês** (`modules/chumbo/montes/services.py`); **UI em pt-BR**.

### 2.3 Estrutura de Diretórios

```
komotores_pcp/                    ← repositório = PLATAFORMA PCP (não "o chumbo")
├── .venv/                        ← ambiente virtual (não versionado)
├── .env / .env.example           ← credenciais (não versionado) + template
├── .gitignore / .dockerignore
├── requirements.txt              ← sempre atualizado, versões fixadas
├── manage.py
├── Dockerfile / entrypoint.sh / worker-entrypoint.sh
├── docker-compose.yml / docker-stack.yml
├── design_system/                ← Design System extraído (fonte de verdade visual)
├── manifest.json / sw.js         ← PWA (instalável no celular — ver seção 7.6)
├── static/ media/ templates/ docs/ mkdocs.yml
│
├── core/                         ← CONFIG do projeto
│   ├── settings.py               ← ÚNICO settings, lê .env; lista módulos em MODULES
│   ├── urls.py                   ← raiz: health, manifest.json(sw), accounts, shell
│   ├── celery.py / wsgi.py / asgi.py
│
├── base/                         ← INFRA da plataforma
│   ├── models.py                 ← BaseModel (created_at/updated_at)
│   ├── managers.py / mixins.py   ← RoleRequiredMixin, PerPageMixin, ModulePermMixin
│   ├── modules.py                ← Registry de módulos + base ModuleManifest
│   ├── middleware.py             ← timeout sessão, injeção de módulos no request
│   └── management/commands/      ← wait_for_db, seed_demo, new_module, reset_demo
│
├── accounts/                     ← AUTH + RBAC global e por módulo
│   ├── models.py                 ← User + Role GLOBAL (admin/operador/...)
│   ├── module_perms.py          ← ModulePermission (role_por_módulo p/ usuário)
│   ├── backends.py / forms.py / views.py / urls.py / admin.py
│
├── shell/                        ← O PORTAL (layout + nav + home agregada)
│   ├── views.py                  ← DashboardView agrega widgets dos módulos via registry
│   ├── context_processors.py     ← injeta menu dinâmico no base.html
│   ├── templates/shell/          ← base_app.html, sidebar, bottom-bar, home
│   └── urls.py
│
├── shared/                       ← CADASTROS CROSS-MÓDULO (usados por >1 módulo)
│   ├── models.py                 ← Setor, Operador, Turno, Maquina (ex.: consumo de chumbo e futuros módulos usam setor/operador/turno)
│   ├── forms.py / views.py / urls.py / admin.py
│   ├── services.py               ← CRUD genérico + seeds compartilhados
│   └── signals.py                ← eventos de domínio publicáveis (setor_criado, etc.)
│
└── modules/                      ← NAMESPACE dos MÓDULOS DE NEGÓCIO
    ├── __init__.py
    ├── registry.py               ← Registro central (preenchido via AppConfig.ready de cada módulo)
    │
    └── chumbo/                   ← MÓDULO 1: Controle de Chumbo
        ├── __init__.py
        ├── apps.py               ← ChumboConfig; no ready() registra o Manifest no registry
        ├── manifest.py           ← Manifest declarativo (ver 2.4)
        ├── urls.py                ← entrypoint do módulo, montado em /chumbo/ no core/urls.py
        │
        │   # sub-apps internas do módulo (todas próprias, prefixadas p/ evitar colisão)
        ├── ligas/                ← Liga (master específica do chumbo)
        ├── lotes/                ← Lote + grade
        ├── montes/               ← Monte, EventoMonte + services (reservar/baixar/mover/estornar)
        ├── saida/                ← Liberação/saída (TransacaoSaida; destino = shared OU interno)
        ├── destinos/             ← Destino de saída (master específica do chumbo: VRLA/Óxido/...)
        ├── consumo/              ← Apontamento de consumo (FIFO + Celery)
        ├── contagem/             ← Inventário físico do chumbo
        └── relatorios/           ← Relatórios + agente IA do chumbo
```

> **Por que `modules/chumbo/lotes/` e não `lotes/` na raiz?** Para que outro módulo futuro possa ter uma entidade chamada "lote" (ex.: lote de óxido) **sem colisão**. As tabelas ficam `chumbo_lotes_batch`, `chumbo_montes_pile`, etc. — namespace natural no BD.
>
> **Por que `shared/` separado de `cadastros/`?** Cadastros que **só o chumbo** usa (Liga, Destino de saída, Modelo de Produto) ficam **dentro** de `modules/chumbo/`. Cadastros que **vários módulos** usam (Setor, Operador, Turno, Máquina) ficam em `shared/` — plataforma.

### 2.4 Manifest e Registry (coração da modularidade)

Cada módulo declara um **Manifest** em `modules/<nome>/manifest.py`:

```python
# modules/chumbo/manifest.py
from base.modules import ModuleManifest, MenuItem, ModuleRole

MANIFEST = ModuleManifest(
    slug="chumbo",
    label="Controle de Chumbo",
    icon="chumbo",                      # token do design system
    order=10,                           # posição no menu
    url_name="chumbo:home",            # entrypoint
    roles=[ModuleRole.ADMIN, ModuleRole.OPERADOR],   # roles que podem acessar
    menu=[
        MenuItem(label="Estoque",   url_name="chumbo:estoque"),
        MenuItem(label="Entrada",   url_name="chumbo:lote_create"),
        MenuItem(label="Consumo",   url_name="chumbo:consumo"),
        MenuItem(label="Relatórios",url_name="chumbo:relatorios", admin_only=True),
    ],
    dashboard_widgets=[                # contribuição p/ a home agregada
        "chumbo.widgets.estoque_widget",
        "chumbo.widgets.saldo_por_liga_widget",
    ],
)
```

O `AppConfig.ready()` de cada módulo chama `modules.registry.register(MANIFEST)`. O **`shell`** consulta o registry em runtime:
- **Menu dinâmico:** mostra apenas módulos/itens que o usuário tem permissão (role global + permissão no módulo).
- **Dashboard agregado:** a home (`shell/`) carrega os `dashboard_widgets` de cada módulo visível — cada módulo contribui com cards, sem o `shell` conhecer os modelos.
- **URLs:** `core/urls.py` inclui `modules.<slug>.urls` dinamicamente a partir do registry (ou via integração explícita — ver §2.7).

### 2.5 Módulo = App Django "auto-contido"

Cada módulo é **removível**: apagar `modules/chumbo/`, remover do `INSTALLED_APPS` e do `core/urls.py` deve ser **suficiente** para o sistema voltar a rodar (perde apenas os dados do chumbo). Para isso:

- O módulo **só** depende de `base`, `accounts`, `shared` (+ Django/stdlib). Nunca de outro módulo.
- Referências de FK **do módulo para `shared`** são permitidas (`consumo` → `shared.Operador`). Referências **de `shared` para um módulo** são **proibidas** (criariam acoplamento da plataforma ao módulo).
- Templates do módulo ficam em `modules/<nome>/<subapp>/templates/` (namespaced).
- Estáticos do módulo em `modules/<nome>/static/<nome>/`.

### 2.6 Permissões por Módulo (RBAC escalável)

- **Role global** (`accounts.User.role`): `ADMIN` (acesso total a tudo) ou `OPERADOR` (base)..Resolve o "super admin" da fábrica.
- **Permissão por módulo** (`accounts.ModulePermission`): `user × module_slug × role_no_modulo`. Permite, por exemplo, um operador ser **admin do módulo chumbo** mas **apenas leitor** num módulo futuro.
- **Mixin `ModulePermMixin`** (em `base/mixins.py`): view filtra `request.module` (slug da URL) e checa `user.has_module_role(slug, role)`. `admin` global sempre passa.
- Manifest declara `roles` exigidos; `shell` e `ModulePermMixin` aplicam.

```python
# accounts/module_perms.py (resumo)
class ModulePermission(BaseModel):
    user = FK(User, related_name='module_perms')
    module_slug = CharField()           # ex.: 'chumbo'
    role = CharField(choices=Role.choices)   # role VÁLIDA dentro daquele módulo
    unique_together = ('user', 'module_slug')
```

### 2.7 URLs e montagem de módulos

Em `core/urls.py` (versão simples / recomendada para começar):

```python
from django.urls import include, path
path('chumbo/', include('modules.chumbo.urls', namespace='chumbo')),
```

> Para chegar ao **auto-registro total** (módulo novo sem editar `core/urls.py`): no `AppConfig.ready()` do módulo, registrar um callback que o `core/urls.py` percorre ao carregar. Começar com o `include` explícito é mais simples e visível; migrar para auto-registro quando houver 3+ módulos e o ganho compense. O `manifest.py` já fica pronto para essa transição.

### 2.8 Padrão interno de cada sub-app

`__init__.py`, `apps.py` (AppConfig; `ready()` conecta signals), `admin.py`, `models.py` (ou `models/` package), `managers.py`, `forms.py`, `views.py`, `urls.py`, `services.py`, `signals.py` (se houver), `tasks.py` (se houver), `tests.py`, `templates/<app>/`, `static/<app>/`.

---

## 3. Requisitos Funcionais

### 3.1 Módulo: Autenticação e Controle de Acesso

| ID | Requisito |
|----|-----------|
| RF01 | Login com email e senha (Django Auth + Session) |
| RF02 | Duas roles: **operador** (visualização parcial) e **admin** (operações totais) |
| RF03 | Timeout de sessão por inatividade (30 min configurável) |
| RF04 | Logout com expurgo de sessão |
| RF05 | UI adapta visibilidade conforme role do usuário logado |
| RF06 | Proteção de views por decorador `@role_required('admin')` |

### 3.2 Módulo: Estoque (Espelho da Grade)

| ID | Requisito |
|----|-----------|
| RF10 | Visualizar estoque por **Liga → Lote → Grade 2D** |
| RF11 | Grade configurável por lote: colunas (1-10) x linhas (1-5) |
| RF12 | Cada célula da grade exibe: kg atual, barras atuais, status operacional, posição (x,y) |
| RF13 | Células com código de cores por status (disponível, reservado, parcial, consumido) |
| RF14 | Três métricas de balanço calculadas: **No Estoque**, **Disponível**, **Reservado** |
| RF15 | Balanço calculado pela SOMA dos montes (não pelo total inicial do lote) |
| RF16 | Arrastar e soltar para trocar posição de montes (admin apenas) |
| RF17 | Histórico de eventos por monte (reserva, movimentação, baixa) |

### 3.3 Módulo: Entrada (Recebimento)

| ID | Requisito |
|----|-----------|
| RF20 | Criar lote em 2 etapas: (1) dados do lote, (2) configurar grade |
| RF21 | Dados do lote: liga, número do lote (único por liga), data de chegada, kg inicial, barras iniciais |
| RF22 | Grade: distribuir kg e barras por posição (até 10x5 = 50 células) |
| RF23 | Exibir soma ao vivo durante preenchimento da grade |
| RF24 | Validar: número do lote único por liga, data não futura, admin apenas |
| RF25 | Soma da grade deve bater com total do lote |

### 3.4 Módulo: Saída (Liberação)

| ID | Requisito |
|----|-----------|
| RF30 | Liberação agrupada: selecionar múltiplos montes e liberar em lote |
| RF31 | Baixa parcial ou total por monte |
| RF32 | Destino da saída: selecionar de lista cadastrável (VRLA, Óxido, Venda, Teleiras, Exportação) |
| RF33 | Gerar grupo de liberação (grupo_liberacao_id) para rastrear operações em lote |
| RF34 | **Estorno** de liberação: restaura saldo do monte, mantém auditoria |
| RF35 | Estorno registra: data, quem estornou, observação |
| RF36 | Status do monte após baixa: PARCIAL (parcial) ou CONSUMIDO (total) |

### 3.5 Módulo: Reserva

| ID | Requisito |
|----|-----------|
| RF40 | Reservar monte sem alterar kg/barras (apenas compromete) |
| RF41 | Registrar destino/setor da reserva + timestamp |
| RF42 | Cancelar reserva com geração de evento histórico |
| RF43 | Reserva em grupo via grupo_reserva_id |
| RF44 | Monte reservado exibe borda amarela na grade |

### 3.6 Módulo: Movimentação

| ID | Requisito |
|----|-----------|
| RF50 | Mover monte do almoxarifado para setor de produção |
| RF51 | Retornar monte do setor para o almoxarifado |
| RF52 | Movimentação parcial (split): criar monte filho em posição virtual (x=99) |
| RF53 | Cada movimentação gera evento no histórico do monte |
| RF54 | Monte no setor exibe visualização atenuada (faded) na grade original |

### 3.7 Módulo: Consumo Diário

| ID | Requisito |
|----|-----------|
| RF60 | Registrar consumo diário com: data, setor, máquina, operador, turno, liga, lote, barras, borra (kg) |
| RF61 | Modo **automático**: sistema seleciona montes por FIFO (data de movimentação ao setor) |
| RF62 | Modo **manual**: usuário escolhe quais montes consumir |
| RF63 | Validar saldo disponível no setor antes de confirmar |
| RF64 | Gerar alocações de consumo detalhadas por monte |
| RF65 | Editar/excluir consumo: admin apenas (reverte alocações, recalcula) |
| RF66 | Campo borra_kg obrigatório (>= 0) |

### 3.8 Módulo: Relatórios

| ID | Requisito |
|----|-----------|
| RF70 | Quatro abas de relatório: Entradas, Saídas, Reservas, Consumo |
| RF71 | Filtro por período (padrão: mês corrente) |
| RF72 | Filtros em cascata por aba (ex: Saídas → destino + liga + setor) |
| RF73 | Card sumário por aba: total kg + total barras |
| RF74 | Drill-down: clicar para ver detalhes e navegar ao registro de origem |
| RF75 | Exportar CSV (admin apenas) com delimitador ponto-e-vírgula e UTF-8 |
| RF76 | Estorno disponível a partir da aba Saídas (admin) |

### 3.9 Cadastros — Dados Mestres (shared vs módulo)

> Split por modularidade (§2.0): cadastros usados por **vários módulos** ficam em `shared/` (plataforma); cadastros **específicos do chumbo** ficam em `modules/chumbo/`. Ambos são acessados pelos CRUDs da UI conforme o escopo do usuário (admin global vê tudo; permissão por módulo restringe os específicos).

| ID | Requisito |
|----|-----------|
| RF80 | CRUD completo para **cadastros shared** (cross-módulo): **Setores, Máquinas, Operadores, Turnos** |
| RF80a | CRUD completo para **cadastros do módulo Chumbo**: **Ligas, Destinos de Saída, Modelos de Produto** |
| RF81 | Ligas (chumbo): nome, chave_cor (azul, amarelo, vermelho, preto, cinza, sem_cor, verde, branco) |
| RF82 | Setores (shared): nome, slug, tipo (producao/saida_direta), ordem |
| RF83 | Destinos (chumbo): VRLA, Óxido, Venda, Teleiras, Exportação (semeados ao instalar o módulo) |
| RF84 | Máquinas (shared): nome, FK setor, ordem |
| RF85 | Operadores (shared): nome, ordem |
| RF86 | Turnos (shared): nome, ordem |
| RF87 | Modelos de Produto (chumbo): nome, polaridade (positiva/negativa), placas_por_grade, tipo |
| RF88 | Soft delete (`is_active = false`) em todos os cadastros (shared e de módulo) |
| RF89 | Reset de dados operacionais de um **módulo** (preserva `shared` + outros módulos) |

### 3.10 Módulo: Inventário Físico (Contagem)

| ID | Requisito |
|----|-----------|
| RF90 | Iniciar contagem física de estoque |
| RF91 | Registrar kg e barras contados por posição da grade |
| RF92 | Comparar contagem com saldo atual do sistema |
| RF93 | Aprovar/rejeitar divergências |
| RF94 | Rascunho salvo localmente (não confirma até aprovação) |

---

## 4. Requisitos Não Funcionais

| ID | Requisito |
|----|-----------|
| RNF01 | **Disponibilidade:** sistema deve funcionar **offline** durante operação no celular, com fila local (Outbox) e sincronização quando houver conexão (PWA + Service Worker) |
| RNF02 | **Performance:** grade de estoque deve carregar em < 2s em rede 3G/4G fraca mesmo com 50+ lotes; LCP < 2.5s; INP < 200ms |
| RNF03 | **Segurança:** validação de role em toda mutation (front + back) |
| RNF04 | **Auditoria:** toda operação em monte gera evento imutável com timestamp e usuário |
| RNF05 | **Rastreabilidade:** todos os movimentos de chumbo são rastreáveis (lote → monte → consumo) |
| RNF06 | **Concorrência:** operações simultâneas usam select_for_update ou optimistic locking via updated_at |
| RNF07 | **UX mobile-first (celular principal):** projeto de interface prioriza telas de **360px–430px**; toques mínimos de 44×44px (padrão PWA/iOS); navegação por bottom-bar; tablets 1200x1920 como uso secundário |
| RNF08 | **Time zone:** armazenar em UTC, exibir em America/Sao_Paulo |
| RNF09 | **Formato data:** dd/MM/yyyy em toda UI |
| RNF10 | **Idempotência:** UUID v4 gerado no cliente para prevenir duplicatas em falhas de rede/reenvio offline |
| RNF11 | **Logs:** estruturais (who fez o quê, quando) armazenados no banco; logs técnicos no stdout Docker |
| RNF12 | **Backup:** PostgreSQL WAL + pg_dump diário |
| RNF13 | **PWA:** app instalável no celular (manifest.json + ícones + service worker), abrível em tela cheia pelo ícone (standalone), com cache de shell e dados essenciais |
| RNF14 | **Acessibilidade mobile:** contraste AA, fonte mínima 16px (evita zoom automático do iOS em inputs), suporte a `prefers-color-scheme` (claro/escuro) |

---

## 5. Modelo de Dados (Django ORM)

### 5.1 Convenções

> **Idiomaticidade Django** (padrão SCSI): nomes de **models, campos, apps, views e comandos em inglês** (ex.: `Pile`, `Batch`, `events`), **UI em pt-BR** (`verbose_name`). Bases abstratas em `base/` reaproveitadas por toda app de domínio.

- **Bases abstratas em `base/models.py`:** `BaseModel` (`created_at`, `updated_at`, `ordering = ('-created_at',)`) herdada por toda model de domínio. (Sem multi-tenant neste projeto — não há corretoras; o isolamento é por **role**, não por tenant.)
- **Custom User:** `accounts.User` herda `AbstractUser` + `BaseModel`, login por **email** (`USERNAME_FIELD = 'email'`, `username = None`), com `Role(TextChoices)` (`OPERATOR`, `ADMIN`). Fixar `AUTH_USER_MODEL = 'accounts.User'` **antes do primeiro migrate** (Sprint 1).
- **Primary key:** `BigAutoField` (padrão Django) — não UUID via SQL manual; мigrar para UUID só se houver necessidade de sync offline distribuído (reavaliar no Sprint 7).
- **Timestamps:** `created_at`/`updated_at` em UTC, exibidos em `America/Sao_Paulo` (`TIME_ZONE` no settings).
- **Soft delete:** `is_active` em dados mestres (ligas, setores, destinos, máquinas, operadores, turnos, modelos) — nunca exclusão física de cadastro.
- **Locking / concorrência:** `select_for_update()` em transações de baixa/reserva/estorno; `updated_at` serve como LWW para sync offline.
- **Money/quantidades:** `DecimalField(max_digits=12, decimal_places=3)` para kg (nunca `FloatField`); `PositiveIntegerField` para barras.
- **Unique por escopo:** `UniqueConstraint(fields=['liga', 'numero'])` para lote; `UniqueConstraint(fields=['lote', 'posicao_x', 'posicao_y'])` para monte.
- **Mixins de view (em `base/mixins.py`):** `RoleRequiredMixin` (`allowed_roles = ('admin',)`) bloqueia mutations sensíveis; `PerPageMixin` para paginação ajustável.
- **Signals:** em `signals.py` da app, conectados no `AppConfig.ready()` (nunca em `models.py`). Ex.: recalcula saldos do lote quando um monte é salvo/deletado.

### 5.2 Schema (referência lógica)

> O SQL abaixo é apenas **referência lógica** de domínio. As tabelas reais seguem o padrão Django `<app>_<model>` em inglês (ex.: `montes_pile`, `lotes_batch`, `cadastros_alloy`) geradas via `makemigrations`/`migrate`. Mantém aqui o SQL para documentar CHECK constraints, snapshots e índices que devem ser replicados no ORM.

```sql
-- ============================================================
-- CORE (accounts + base)
-- ============================================================

CREATE TABLE core_usuario (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL,       -- FK para auth do Django ou sistema próprio
    nome            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('operador', 'admin')),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- CADASTROS (Dados Mestres)
-- ============================================================

CREATE TABLE cadastros_liga (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    chave_cor       VARCHAR(20) NOT NULL CHECK (chave_cor IN ('azul','amarelo','vermelho','preto','cinza','sem_cor','verde','branco')),
    is_active       BOOLEAN DEFAULT true,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE cadastros_setor (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    tipo            VARCHAR(20) NOT NULL CHECK (tipo IN ('producao', 'saida_direta')),
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE cadastros_destino_saida (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

-- Seeds iniciais: VRLA, Oxido, Venda, Teleiras, Exportacao

CREATE TABLE cadastros_maquina (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    setor_id        UUID NOT NULL REFERENCES cadastros_setor(id),
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE cadastros_operador (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE cadastros_turno (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE cadastros_modelo_produto (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(100) NOT NULL,
    polaridade      VARCHAR(10) CHECK (polaridade IN ('positiva', 'negativa')),
    placas_por_grade INTEGER,
    tipo            VARCHAR(20) DEFAULT 'grade',
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

-- ============================================================
-- OPERACIONAIS
-- ============================================================

CREATE TABLE lotes_lote (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    liga_id         UUID NOT NULL REFERENCES cadastros_liga(id),
    numero_lote     VARCHAR(50) NOT NULL,
    data_chegada    DATE NOT NULL,
    peso_inicial_kg NUMERIC(12,3) NOT NULL,
    barras_iniciais INTEGER NOT NULL,
    colunas_grade   INTEGER NOT NULL DEFAULT 10 CHECK (colunas_grade BETWEEN 1 AND 10),
    linhas_grade    INTEGER NOT NULL DEFAULT 5  CHECK (linhas_grade BETWEEN 1 AND 5),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id),
    UNIQUE (liga_id, numero_lote)
);

CREATE TABLE montes_monte (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lote_id         UUID NOT NULL REFERENCES lotes_lote(id) ON DELETE CASCADE,
    peso_atual_kg   NUMERIC(12,3) NOT NULL DEFAULT 0,
    barras_atuais   INTEGER NOT NULL DEFAULT 0,
    posicao_x       INTEGER NOT NULL CHECK (posicao_x BETWEEN 0 AND 99),
    posicao_y       INTEGER NOT NULL CHECK (posicao_y BETWEEN 0 AND 4),
    status          VARCHAR(20) NOT NULL DEFAULT 'DISPONIVEL'
                    CHECK (status IN ('DISPONIVEL','RESERVADO','PARCIAL','CONSUMIDO')),
    reservado_para  VARCHAR(100),
    reservado_em    TIMESTAMPTZ,
    setor_reserva_id UUID REFERENCES cadastros_setor(id),
    grupo_reserva_id UUID,
    localizacao     VARCHAR(20) NOT NULL DEFAULT 'almoxarifado'
                    CHECK (localizacao IN ('almoxarifado', 'setor')),
    setor_id        UUID REFERENCES cadastros_setor(id),
    movido_setor_em TIMESTAMPTZ,
    monte_origem_id UUID REFERENCES montes_monte(id),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (lote_id, posicao_x, posicao_y)
);

CREATE TABLE montes_evento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monte_id        UUID NOT NULL REFERENCES montes_monte(id) ON DELETE CASCADE,
    tipo            VARCHAR(30) NOT NULL CHECK (tipo IN (
                        'RESERVA','CANCELAMENTO_RESERVA','BAIXA_PARCIAL','BAIXA_TOTAL',
                        'MOVIDO_PARA_SETOR','DEVOLVIDO_ALMOXARIFADO','ESTORNO',
                        'SPLIT_CRIADO','CONSUMO_ALOCADO'
                    )),
    dados           JSONB,                    -- payload flexível com detalhes do evento
    created_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE saida_transacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monte_id        UUID NOT NULL REFERENCES montes_monte(id),
    peso_baixado_kg NUMERIC(12,3) NOT NULL,
    barras_baixadas INTEGER NOT NULL,
    destino_saida_id UUID NOT NULL REFERENCES cadastros_destino_saida(id),
    setor_id        UUID REFERENCES cadastros_setor(id),
    data_transacao  TIMESTAMPTZ NOT NULL DEFAULT now(),
    grupo_liberacao_id UUID,
    observacao      TEXT,
    estornada       BOOLEAN DEFAULT false,
    estornada_em    TIMESTAMPTZ,
    estornada_por_id UUID REFERENCES core_usuario(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id)
);

CREATE TABLE consumo_apontamento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_consumo    DATE NOT NULL,
    liga_id         UUID NOT NULL REFERENCES cadastros_liga(id),
    lote_id         UUID NOT NULL REFERENCES lotes_lote(id),
    setor_id        UUID NOT NULL REFERENCES cadastros_setor(id),
    maquina_id      UUID REFERENCES cadastros_maquina(id),
    operador_id     UUID REFERENCES cadastros_operador(id),
    turno_id        UUID REFERENCES cadastros_turno(id),
    modelo_produto_id UUID REFERENCES cadastros_modelo_produto(id),
    barras          INTEGER NOT NULL,
    peso_kg         NUMERIC(12,3) NOT NULL,
    borra_kg        NUMERIC(10,3) NOT NULL DEFAULT 0,
    modo_selecao    VARCHAR(20) NOT NULL DEFAULT 'automatico' CHECK (modo_selecao IN ('automatico','manual')),
    observacoes     TEXT,
    -- Snapshots para auditoria (imutáveis)
    nome_operador   VARCHAR(255),
    nome_turno      VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT now(),
    created_by_id   UUID REFERENCES core_usuario(id),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE consumo_alocacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apontamento_id  UUID NOT NULL REFERENCES consumo_apontamento(id) ON DELETE CASCADE,
    monte_id        UUID NOT NULL REFERENCES montes_monte(id),
    barras_baixadas INTEGER NOT NULL,
    peso_baixado_kg NUMERIC(12,3) NOT NULL,
    kg_por_barra_snapshot NUMERIC(10,5),
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. Regras de Negócio

### 6.1 Status do Monte

| Status | Significado |
|--------|-------------|
| DISPONIVEL | Livre para reserva/baixa/movimentação |
| RESERVADO | Comprometido; kg/barras inalterados |
| PARCIAL | Parcialmente baixado; permanece na mesma posição |
| CONSUMIDO | Totalmente consumido; kg=0, barras=0; célula visível mas inativa |

### 6.2 Balanço (Fonte da Verdade)

O saldo operacional é **SEMPRE a soma de todos os montes** do lote. Os valores `peso_inicial_kg` e `barras_iniciais` do lote são apenas auditoria (snapshot da chegada).

### 6.3 Transições de Estado

```
DISPONIVEL ──reservar──► RESERVADO ──cancelar reserva──► DISPONIVEL
DISPONIVEL ──baixa parcial──► PARCIAL
DISPONIVEL ──baixa total──► CONSUMIDO
PARCIAL ──baixa parcial──► PARCIAL (kg/barras reduzidos)
PARCIAL ──baixa total──► CONSUMIDO
DISPONIVEL ──mover setor──► DISPONIVEL (localizacao=setor)
SETOR ──devolver──► DISPONIVEL (localizacao=almoxarifado)
QUALQUER ──estorno──► Estado anterior (restaura kg/barras)
```

### 6.4 Matriz de Permissões

> **Dois níveis (§2.6):** (a) **Role global** do usuário — `ADMIN` (acesso total a todos os módulos) ou `OPERADOR` (base). (b) **Permissão por módulo** (`ModulePermission`) — define o papel do usuário **dentro** de um módulo específico (ex.: `OPERADOR` no chumbo, `ADMIN` num módulo futuro). A matriz abaixo vale **dentro do módulo Chumbo**; `ADMIN` global sempre vira `admin` em qualquer módulo.

| Ação (no módulo Chumbo) | operador | admin |
|------|:--------:|:-----:|
| Visualizar estoque | ✓ | ✓ |
| Visualizar relatórios | ✓ | ✓ |
| Registrar consumo | ✓ | ✓ |
| Reservar / Cancelar reserva | ✗ | ✓ |
| Baixa / Liberação | ✗ | ✓ |
| Mover monte | ✗ | ✓ |
| Estornar | ✗ | ✓ |
| Editar / Excluir consumo | ✗ | ✓ |
| CRUD cadastros do chumbo | ✗ | ✓ |
| CRUD cadastros `shared` | ✗ | ✓ |
| Exportar CSV | ✗ | ✓ |
| Trocar posição de montes (drag) | ✗ | ✓ |
| Gerenciar permissões de usuários no módulo | ✗ | ✓ |

> **Acesso à plataforma:** `shell` (home agregada) e `accounts` (perfil próprio) são visíveis a todo autenticado; o menu mostra apenas módulos em que o usuário tem permissão (ou é `admin` global).

### 6.5 Regras de Consumo

1. **Montes elegíveis:** localizacao=setor, setor corresponde, mesma liga/lote, barras>0, status!=CONSUMIDO
2. **FIFO automático:** ordenar por movido_setor_em ASC
3. **Manual:** usuário define ordem dos montes
4. **Validação:** se saldo no setor < barras solicitadas → erro, nada salvo
5. **Editar/Excluir:** admin apenas; reverte alocações antigas, recalcula saldos
6. **Borra (borra_kg):** obrigatório, >= 0

### 6.6 Regras de Reserva

1. Reserva **não** altera kg/barras do monte
2. Destino/setor obrigatório
3. Cancelamento gera evento CANCELAMENTO_RESERVA
4. Grupo de reserva via grupo_reserva_id (UUID)

### 6.7 Regras de Movimentação

1. Mover para setor: preenche setor_id, movido_setor_em, localizacao='setor'
2. Devolver: limpa setor_id, localizacao='almoxarifado'
3. Split (movimento parcial): monte filho na posição virtual (x=99), monte original reduz
4. Split gera evento SPLIT_CRIADO

### 6.8 Regras de Estorno

1. Restaura saldo do monte (kg + barras)
2. Marca transacao_saida.estornada = true
3. Registra estornada_por, estornada_em
4. Gera evento ESTORNO no monte
5. Não pode estornar se monte já foi consumido
6. **Reprocessa status do monte com a regra `||`** (ver §6.9 ARC-01): se barras==0 **ou** peso<=epsilon → CONSUMED (não `&&`)

### 6.9 Aprendizados do Sistema Legado — Regras Anti-Regressão (ARC)

> A análise do sistema legado (`ANALISE_sistema_antigo.md`, 21 itens) catalogou bugs e fragilidades reais que **NÃO podem reaparecer** no novo projeto. Cada aprendizado vira uma regra canônica **ARC-NN** (Anti-Regressão), referenciável a partir das sprints e dos testes.

#### Domínio / Estado dos montes

- **ARC-01 — Peso residual fantasma (crítico).** O status `CONSUMED` é atingido quando `barras <= 0` **OU** `peso_kg <= EPSILON` (ε = 0,0005 kg) — **nunca `&&`**. O sistema legado usava `barras<=0 && peso<=0`, deixando pesos como `0,002` presos sem nunca zerar. Regra: ao consumir/estornar, recalcular com `||` e, se CONSUMED, forçar `peso_kg = 0` e `barras = 0` (limpeza explícita). Aplica-se a `consumo.services`, `saida.services.baixa` e `saida.services.estornar`.
- **ARC-02 — Validação de existência da liga (race de criação de lote).** Criar lote dentro de `transaction.atomic()` com `select_for_update` na liga (ou FK com `PROTECT`). O legado verificava a liga e só depois criava o lote → existia janela para liga ser apagada entre check e insert, gerando órfão. Regra: validar via FK constraint + tratar `IntegrityError` com mensagem útil; nunca "consultar depois inserir".
- **ARC-03 — kg/barras consistente na liberação parcial (UI).** No formulário de liberação parcial, sempre que as barras mudam, **recalcular kg** — exceto SE o usuário já editou manualmente o kg **E** não tocou nas barras desde então. O legado congelava o kg após um único toque manual e des sincronizava. Regra: flag `kg_manual_invalidado` que zera quando `barras` muda (HTMX ressecalca o kg). Validar no submit `kg ≈ barras × peso_por_barra` (ε de 1%) ou exige confirmação.
- **ARC-04 — Reserva órfã na devolução ao almoxarifado.** Devolver monte ao almoxarifado **deve** preservar OU limpar explicitamente os campos de reserva; escolha seja declarada e testada. Legado deixava `reserved_for`/`reserved_at`/`reserved_sector_id` esquecidos sem saber se a reserva ainda existia. Regra: `montes.services.devolver_almoxarifado()` ou mantém reserva (status=RESERVADO, borda amarela) **ou** cancela a reserva + gera `CANCELAMENTO_RESERVA` — nunca "silenciosamente órfão". Documentar o escolhido no `tests.py`.

#### Consumo

- **ARC-05 — Lote sem saldo não aparece no select de consumo.** O select de "Lote" no apontamento de consumo lista apenas lotes que possuem montes elegíveis no setor selecionado (`localizacao='setor'`, mesmo setor, `barras>0`, status≠CONSUMED). Legado listava todos → erro ao salvar.
- **ARC-06 — Atomicidade do consumo (multi-monte).** Toda baixa de consumo (vários montes numa operação) acontece dentro de **uma única `transaction.atomic()`** com `select_for_update()` nos montes envolvidos. Legado enfileirava syncs por monte; se um falhasse, ficava inconsistente entre local e servidor. No Django, o `transaction.atomic` resolve a atomicidade; o sync offline fica em camada genérica (`base/sync/`, Sprint 7).
- **ARC-07 — `peso_por_barra` nunca retorna 0 silenciosamente.** Helper de cálculo de kg/barra lança `AppError` (ou `ValidationError`) quando `barras<=0` ou `peso_kg` não-finito — **não** retorna 0 (legado mascarava divisão por zero).

#### Sync / Offline (camada genérica em `base/sync/`)

> A camada de sync é **da plataforma**, usada por qualquer módulo. As regras abaixo valem para todos.

- **ARC-08 — Cursor de pull delta robusto (não perder registros).** O pull delta usa cursor composto `(updated_at, id)` e consulta por `(updated_at > cursor_at) OR (updated_at = cursor_at AND id > cursor_id)` — **não** `updated_at > cursor_at` puro (legado perdia registros do mesmo milissegundo do cursor). Em Django: ordenar por `('updated_at','id')`, paginar, salvar cursor do último registro.
- **ARC-09 — LWW com desempate determinístico.** Last-Writer-Wins desempata por `updated_at` e, em empate dehoras, **maior `id`** vence (regra simples, determinística). Documentar para o usuário que conflitos offline simultâneos no mesmo registro perdem um lado — aceitável para este domínio (operação de centavos/kg).
- **ARC-10 — Sync ao voltar online: checar auth primeiro.** Ao `ononline`, **antes** de `flush`, validar sessão válida. Legado chama `flushOutbox` com sessão expirada → erros silenciosos. Regra: se sessão expirou, redirecionar ao login e **preservar** o outbox (não descartar); só flushear quando autenticado.
- **ARC-11 — Não compartilhar estado de sync entre abas/dispositivos.** Flags como `pausedForAuth` vivem em `sessionStorage`/contexto **por aba** (não em singleton de módulo como o legado, que pausava uma aba pela outra). Em Django front (Alpine/HTMX): estado de sync isolado por SW context (Clients.claim() por aba).
- **ARC-12 — Flushear outbox em loop até esvaziar (não chamada dupla hardcoded).** O legado chamava `flushOutbox()` duas vezes seguidas para "drenar em batches de 50". Regra: loop `while outbox não vazio AND batch_enviado > 0`, com **limite de iterações** (ex.: 10) e break ao estabilizar — documentado. Evita chamadas fixas e bugs de "só dois batches".
- **ARC-13 — Não receber de volta eventos internos via realtime.** Eventos `MOVED_TO_SECTOR`, `DEVOLVIDO_ALMOXARIFADO`, `SPLIT_CRIADO`, `CONSUMO_ALOCADO` são **saídas** e não precisam voltar por realtime (foram gerados localmente e enviados via outbox). No Django, auditoria dos `EventoMonte` é local + servidor; "realtime" (SSE/poll) só puxa **resultado** das entidades (monte, lote), não os eventos internos.

#### Mobile / UX

- **ARC-14 — Grade 2D não fixa colunas em telas estreitas.** A NUNCA usar `grid-template-columns: repeat(7, 96px)` fixo (legado: 7×96=672px, obrigava scroll horizontal até num lote único). Regra: no celular, grade com `min-cell=40px`, scroll horizontal + pinch-zoom; em < 400px, oferecer **modo compacto** (1 coluna, lista de montes por posição). Célula nunca < 40px. Testar em emulação de iPhone SE (375px).
- **ARC-15 — Dashboard sem truncamento cego de ligas.** Não cortar em "primeiras 6 ligas" (legado: `rows.slice(0,6)` escondia o resto sem avisar). Regra: dashboard mostra **todas** as ligas ***************************************************com scroll** ou "**+ N ligas**" que expande; nunca omite silenciosamente.
- **ARC-16 — Texto instrutivo curto, sem siglas.** Instruções na grade devem ser de **1 linha** e **sem siglas inexplicadas** (legado usava "RES", "SET"). Regra: usar ícones + rótulos claros; qualquer sigla expansível via tooltip/`title`. Preferir dica contextual por monte ao invés de banner permanente de 3 linhas.
- **ARC-17 — Botão flutuante respeita `safe-area-inset-bottom`.** Ações flutuantes (FAB "+") devem usar `env(safe-area-inset-bottom)` e não `margin-bottom: -24px` que o legado usava (sobrepunha nav nativa Android, toques fantasmas). Regra: posição final dentro da safe-area, nunca negativa por baixo da nav.

#### Validação / Robustez de views

- **ARC-18 — Edição de registro possivelmente removido.** Tela de edição de consumo (vindo de relatório com link antigo) deve usar `get_object_or_404` e, se o registro sumiu, mostrar **erro claro** ("registro não encontrado, pode ter sido excluído") — não preencher form parcial. Legado carregava parcial sem aviso.
- **ARC-19 — Reset por módulo (não global).** "Reset de dados operacionais" (RF89) **só**	apaga dados do módulo atual (Chumbo), preserva `shared` e outros módulos. Legado tinha reset global. Regra: comando `python manage.py reset_modulo chumbo` (ou botão admin com confirmação dupla) remove `lotes`, `montes`, `saida`, `consumo`, `contagem`, **eventos** do módulo — nunca toca `shared`.
- **ARC-20 — Filtro por modelo de produto no relatório de consumo.** `modelo_produto_id` existe no apontamento → o relatório de consumo deve permitir filtrar por modelo (legado tinha o campo mas não o filtro). Sprint 6 deve incluí-lo nos "filtros em cascata".

> **Como usar ARC-NN:** cada sprint relevante cita as ARCs que implementa (ex.: Sprint 4 cobre ARC-01/03/04, Sprint 5 cobre ARC-05/06/07, Sprint 7 cobre ARC-08 a ARC-13). Os **testes automáticos** do módulo devem incluir casos nomeados `test_arc01_consumed_com_peso_residual`, `test_arc08_pull_delta_nao_perde_registros`, etc. — rastreando a origem da regra.

---

## 7. Design System

### 7.1 Fonte de Referência

Sugerido: extrair design system de **Aura Build** (https://www.aura.build/) ou **Linear** (https://linear.app).

### 7.2 Esquema de Cores (Grade de Estoque)

| Estado da Célula | Cor |
|------------------|-----|
| Disponível | Fundo limpo / verde claro |
| Reservado | Borda amarela |
| Parcial | Neutro (cinza claro) |
| Consumido | Cinza escuro / inativo |
| Movido ao setor | Atenuado (opacidade reduzida) |

### 7.3 Cores das Ligas (chave_cor)

| Chave | Cor |
|-------|-----|
| azul | Azul |
| amarelo | Amarelo |
| vermelho | Vermelho |
| preto | Preto |
| cinza | Cinza |
| sem_cor | Neutro |
| verde | Verde |
| branco | Branco |

### 7.4 Responsividade (mobile-first real)

O celular é o dispositivo de uso principal. breakpoints por **mobile-first**:

| Breakpoint | Largura | Layout |
|------------|---------|--------|
| `xs` (celular) | 360–430px | **Alvo principal.** Bottom-bar de navegação, grade 2D com scroll horizontal "pinça" (pinch-zoom), cards empilhados, formulários em tela cheia |
| `sm` (celular grande/phablet) | 431–767px | Mesma base xs com mais respiro, grade um pouco maior |
| `md` (tablet retrato) | 768–1023px | Sidebar colapsável, grade expandida |
| `lg` (tablet/1200x1920) | 1024px+ | Layout completo com sidebar fixa |
| `xl` (desktop) | 1280px+ | Grade expandida, painéis laterais |

### 7.5 Diretrizes de UI móvel

- **Tap targets:** mínimo 44×44px (botões, células da grade, ícones)
- **Navegação principal:** bottom-bar fixa com 4–5 itens (Estoque, Entrada, Consumo, Relatórios, Mais)
- **Grade 2D no celular:** pinch-zoom + scroll horizontal, células nunca abaixo de 40px; popover com detalhes ao toque (não hover)
- **Formulários:** inputs `inputmode` corretos (numérico para kg/barras), `autocomplete="off"`, evitar `type=number` (problemas em mobilea usar `type="text"` + `inputmode="decimal"`), destaque do campo ativo
- **Confirmações:** modais nativos ou bottom-sheet (não `alert/confirm`)
- **Feedback:** toasts via HTMX/Sonner-equivalent no topo, vibração curta (`navigator.vibrate(20)`) em ações críticas (liberação, estorno)
- **Evitar reloads pesados:** HTMX swaps parciais, skeletons de carregamento
- **Sem depender de hover:** qualquer ação acessível por toque/longo-pressionar

### 7.6 PWA (instalável no celular)

- `manifest.json` (name, short_name, theme_color, background_color, ícones 192/512, display=standalone, start_url)
- Service Worker com Workbox: cache de app shell (HTML/CSS/JS/ícones) + estratégico para dados críticos
- Banner "Adicionar à tela de inicial" (instalável)
- Funcionamento offline real: fila local (Outbox em IndexedDB) das mutações, sincronização quando volta online (Background Sync API)
- Compatível com iOS Safari (apple-touch-icon, meta `apple-mobile-web-app-capable`)

---

## 8. Sprints

### Sprint 1: Plataforma (core + base + accounts + shell + shared)

**Objetivo:** Entregar a **plataforma** rodando, autenticação, RBAC por módulo e o **sistema de módulos** (registry + manifest + shell com nav dinâmica). Ao fim desta sprint, a home mostra "nenhum módulo instalado" e está pronta para receber o chumbo.

- [ ] Criar projeto Django com Docker Compose (Django + PostgreSQL + RabbitMQ + Redis)
- [ ] `core/` (settings único via `django-environ`, `celery.py` com autodiscover, wsgi/asgi, urls com `/health/` + `manifest.json`/`sw.js`)
- [ ] `accounts/`: `User` customizado por email + `EmailBackend` + `Role.TextChoices` (ADMIN/OPERADOR) — **`AUTH_USER_MODEL` fixado antes do primeiro migrate** + `ModulePermission` model (user × module_slug × role)
- [ ] `base/`: `BaseModel`, `RoleRequiredMixin`, `PerPageMixin`, **`ModulePermMixin`**, **`base/modules.py`** (`ModuleManifest`, `MenuItem`, `ModuleRole` + `register()`) + management command `wait_for_db`
- [ ] `modules/` namespace + `modules/registry.py` (registro preenchido no `AppConfig.ready()` de cada módulo; lido por `shell`)
- [ ] `shared/`: models `Setor`, `Operador`, `Turno`, `Maquina` + admin + CRUD + seeds + `signals.py` (eventos publicáveis)
- [ ] `shell/`: `base_app.html` mobile-first (bottom-bar no celular, sidebar em `lg+`), `DashboardView` agregando widgets do registry, **context processor que injeta menu dinâmico** só com módulos permitidos ao usuário
- [ ] Configurar `.env`/`.env.example`, `.gitignore`, `.dockerignore`, `requirements.txt`
- [ ] `Dockerfile` + `entrypoint.sh` (wait_for_db + migrate com **advisory lock** + collectstatic) + `worker-entrypoint.sh` + `docker-compose.yml`
- [ ] Management commands: `seed_demo` (Faker pt_BR), `createsuperuser`
- [ ] Tela de login/perfil + design system extraído (`design_system/design-system.html`)
- [ ] PWA básico: `manifest.json` + service worker (Workbox) cacheando app shell
- [ ] Endpoint `/health/` para healthcheck
- [ ] Tela "Gerenciar permissões de usuários por módulo" (admin global)
- [ ] Deploy inicial em VPS de homologação (Swarm + Traefik)
- [ ] **Validação da modularidade:** com `modules/` vazio, o sistema sobe, login funciona e home exibe "sem módulos" — base sólida para receber qualquer módulo.

### Sprint 2: Módulo Chumbo — Setup + Cadastros do módulo + Ligas/Grade

**Objetivo:** Criar o **módulo Chumbo** (manifest, urls montadas em `/chumbo/`, permissões) e os cadastros **específicos** do chumbo (Ligas, Destinos, Modelos de Produto). Os cadastros `shared` (Setor/Operador/Turno/Máquina) já existem da Sprint 1.

- [ ] `modules/chumbo/` (package): `apps.py` (registra `MANIFEST` no `ready()`), `manifest.py` (slug, menu, widgets placeholders), `urls.py` em `/chumbo/`
- [ ] `modules/chumbo/ligas/`: model Liga + CRUD + seletor de cor (chave_cor)
- [ ] `modules/chumbo/destinos/`: model Destino + CRUD + seed (VRLA, Óxido, Venda, Teleiras, Exportação)
- [ ] `modules/chumbo/modelos/`: model ModeloProduto + CRUD (polaridade, placas_por_grade)
- [ ] **Widget de dashboard do módulo** (saldo por liga) aparecendo na home agregada do `shell`
- [ ] `ModulePermMixin` aplicado em todas as views do módulo; menu do chumbo aparece só a quem tem permissão (ou é admin global)
- [ ] Soft delete (`is_active`) em todos os cadastros do módulo
- [ ] Modal/página de CRUD com HTMX (excluir sem refresh), mobile-first

### Sprint 3: Módulo Chumbo — Entrada + Grade de Estoque

**Objetivo:** Receber chumbo e visualizar a grade 2D. · **ARCs cobertas:** ARC-02 (liga válida em transação), ARC-14 (grade não fixa), ARC-16 (texto curto), ARC-17 (safe-area).

- [ ] `modules/chumbo/lotes/`: model Batch + criação em 2 etapas; criação em `transaction.atomic` com `select_for_update` na liga (ARC-02)
- [ ] `modules/chumbo/montes/`: models Pile + PileEvent
- [ ] Formulário etapa 1: dados do lote (liga, número, data, kg/barras)
- [ ] Formulário etapa 2: grade interativa (10x5) com preenchimento célula a célula
- [ ] Soma ao vivo durante preenchimento
- [ ] Validações: lote único por liga, data não futura, soma bate
- [ ] View de estoque: liga → lote → grade 2D **responsiva** (min-cell 40px, pinch-zoom, modo compacto < 400px — ARC-14)
- [ ] Células com cor por status + popover com detalhes (toque, não hover)
- [ ] Três métricas de balanço (Estoque, Disponível, Reservado)

### Sprint 4: Módulo Chumbo — Saída + Reserva + Movimentação

**Objetivo:** Operações de saída, reserva e movimentação de montes. · **ARCs cobertas:** ARC-01 (CONSUMED com `||`), ARC-03 (kg/barras na liberação parcial), ARC-04 (reserva não órfã na devolução).

- [ ] `modules/chumbo/saida/`: model Saída (FK para `modules.chumbo.destinos.Destino`)
- [ ] Seleção de múltiplos montes na grade
- [ ] Liberação agrupada com destino; UI de parcial recalcula kg nas mudanças de barras (ARC-03)
- [ ] Baixa parcial/total por monte; reprocessa status com `barras<=0 OU peso<=EPSILON` → CONSUMED + zera residual (ARC-01)
- [ ] Estorno de liberação; mesma regra de status (ARC-01, §6.8 item 6)
- [ ] `modules/chumbo/montes/services.py`: reservar() + cancelar_reserva()
- [ ] `devolver_almoxarifado()` **declarada**: ou preserva reserva (borda amarela) **ou** cancela + evento — testado (ARC-04)
- [ ] UI de reserva: painel lateral ao clicar no monte
- [ ] Histórico de eventos por monte (modal/timeline)
- [ ] Movimentação: mover para setor (`shared.Setor`) + devolver ao almoxarifado
- [ ] Split (movimentação parcial) com monte filho

### Sprint 5: Módulo Chumbo — Consumo Diário

**Objetivo:** Apontamento de consumo da produção. · **ARCs cobertas:** ARC-01 (status), ARC-05 (select de lote só com saldo), ARC-06 (atomicidade multi-monte), ARC-07 (kg/barra sem zero silencioso), ARC-18 (edição de registro removido), ARC-20 (filtro por modelo).

- [ ] `modules/chumbo/consumo/`: models Apontamento + Alocaçao (FK p/ `shared`)
- [ ] Formulário de consumo: data, setor, máquina, operador, turno, liga, lote, barras, borra
- [ ] **Select de "Lote" lista só lotes com montes elegíveis no setor** (ARC-05)
- [ ] Modo automático (FIFO por data de movimentação)
- [ ] Modo manual (selecionar montes específicos)
- [ ] Validação de saldo no setor antes de confirmar
- [ ] Alocações detalhadas geradas automaticamente; **baixa atômica** `transaction.atomic` + `select_for_update` em todos os montes (ARC-06); status via `||` (ARC-01)
- [ ] `peso_por_barra` lança `AppError` em divisão inválida (ARC-07)
- [ ] Editar consumo (admin): `get_object_or_404` + erro claro se registro sumiu (ARC-18); reverte alocações antigas, recalcula
- [ ] Excluir consumo (admin): com confirmação e reversão

### Sprint 6: Módulo Chumbo — Relatórios

**Objetivo:** Visualização e exportação de relatórios. · **ARCs cobertas:** ARC-20 (filtro por modelo de produto).

- [ ] `modules/chumbo/relatorios/`: 4 abas (Entradas, Saídas, Reservas, Consumo)
- [ ] Filtro por período (date range picker)
- [ ] Filtros em cascata por aba; **Consumo inclui filtro por Modelo de Produto** (ARC-20)
- [ ] Card sumário (total kg + total barras); **dashboard Poe todas as ligas com scroll** (não corta em 6 — ARC-15)
- [ ] Tabela com dados detalhados (sortable)
- [ ] Drill-down: modal com detalhes; link para editar consumo usa `get_object_or_404` (ARC-18)
- [ ] Export CSV (admin, UTF-8 BOM, semicolon delimiter)
- [ ] LangChain agent (do módulo): "Quanto chumbo foi consumido esta semana?" → resposta em PT-BR

### Sprint 7: Módulo Chumbo — Inventário Físico + Polimento

**Objetivo:** Contagem física + refinamentos finais. · **ARCs cobertas:** ARC-08 (cursor delta), ARC-09 (LWW desempate), ARC-10 (auth antes de flush), ARC-11 (sync por aba), ARC-12 (loop flush), ARC-13 (realtime só resultado), ARC-19 (reset por módulo).

- [ ] `modules/chumbo/contagem/`: contagem física por lote
- [ ] Registrar kg/barras contados por posição da grade
- [ ] Comparar com saldo atual
- [ ] Aprovar/rejeitar divergência
- [ ] **Reset por módulo**: `python manage.py reset_modulo chumbo` (apaga dados do chumbo, preserva `shared` + outros módulos) — **nunca global** (ARC-19)
- [ ] **Offline/Outbox (camada genérica `base/sync/`)**:
  - [ ] Cursor de pull delta composto `(updated_at, id)` com `>=` — não perder registros do mesmo ms (ARC-08)
  - [ ] LWW com desempate por maior `id` em empate dehoras; documentar limitação ao usuário (ARC-09)
  - [ ] Ao voltar online: validar sessão **antes** de flush; se expirou, ir ao login e **preservar** outbox (ARC-10)
  - [ ] Estado de sync isolado por aba (sessionStorage/SW client) — não singleton compartilhado (ARC-11)
  - [ ] Loop `while outbox não vazio AND batch_enviado>0` com limite de iterações (ARC-12)
  - [ ] Realtime (SSE/poll) puxa só **entidades** (monte, lote); **não** eventos internos (ARC-13)
  - [ ] Idempotência por UUID do cliente (`RNF10`)
- [ ] **Testes automáticos nomeados por ARC** (rastreabilidade): `test_arc01_*`, `test_arc08_*`, etc.
- [ ] **Testes mobile:** Lighthouse PWA + Performance ≥ 90, auditoria em emulação 3G/iPhone SE (375px)
- [ ] Testes de aceitação (manuais) em celular real
- [ ] Revisão de segurança (CSRF, SQL injection, XSS)
- [ ] Performance tuning (N+1 queries, índices)
- [ ] Deploy final em produção (Docker Swarm + Traefik + Cloudflare)

---

## 9. Arquitetura de Deploy

### 9.1 Dockerfiles e entrypoints (padrão SCSI)

- **`Dockerfile`** único (base `python:3.13-slim`): copia `requirements.txt` antes do código (cache de layers), instala `build-essential libpq-dev`, expõe 8000, entrypoint `entrypoint.sh`.
- **`entrypoint.sh`** (serviço web):
  1. `python manage.py wait_for_db --timeout 90` (management command próprio)
  2. **Migrate com advisory lock do Postgres** (`pg_try_advisory_lock(1)`): em Swarm com múltiplas réplicas, só uma roda `migrate` por vez; as demais aguardam o lock e seguem. Resolve o race no startup do Swarm (que ignora `depends_on` em runtime).
  3. `collectstatic --noinput --clear`
  4. `exec "$@"` (recebe o comando do compose/stack — `runserver` em dev, `gunicorn` em prod)
- **`worker-entrypoint.sh`** (celery worker/beat): sem migrate/collectstatic — só `wait_for_db` + `exec "$@"`. Evita concorrência de migrations no worker.
- **`.dockerignore`**: excluir `.venv/`, `media/`, `staticfiles/`, `.env`, `db.sqlite3`, `__pycache__`, `.git`.

### 9.2 Desenvolvimento (Docker Compose)

```
Serviços:
  - app          (runserver 0.0.0.0:8000, volume .:/app)
  - db           (postgres:16, healthcheck pg_isready)
  - rabbitmq     (rabbitmq:3-management, portas 5672/15672)
  - redis        (redis:7, result backend + cache)
  - celery_worker (celery -A core worker -l info)
  - celery_beat   (celery -A core beat --scheduler django_celery_beat...DatabaseScheduler)

Volumes: pg_data, media_data (compartilhado entre app e celery p/ media)
env_file: .env  |  depends_on com condition: service_healthy (db)
```

> Em dev local sem Docker, `DATABASE_URL` cai para SQLite (default no settings) — útil para validar telas rapidamente.

### 9.3 Produção (Docker Swarm — `docker-stack.yml`)

```
Serviços:
  - traefik        (replicas 1, node.role==manager, dashboard com basic auth)
  - app            (gunicorn core.wsgi, replicas 2, update start-first/rollback stop-first)
  - db             (postgres:16, replicas 1, volume pg_data)
  - rabbitmq       (replicas 1, volume rabbitmq_data, healthcheck check_port_connectivity)
  - redis          (appendonly, maxmemory 256mb allkeys-lru)
  - celery_worker  (replicas 2, entrypoint worker-entrypoint.sh)
  - celery_beat    (replicas 1, DatabaseScheduler)

Redes overlay:
  - traefik_public          (external, compartilhada com Traefik)
  - komotores_pcp_internal  (overlay, internal=true — app↔db, sem internet)
  - komotores_pcp_egress    (overlay — celery/ia, acesso à internet)

Volumes: pg_data, media_data, static_data, letsencrypt, redis_data, rabbitmq_data

Secrets: CLOUDFLARE_DNS_API_TOKEN (external, via docker secret)

Imagens: ghcr.io/<owner>/komotores-pcp:latest (GHCR) — repo da PLATAFORMA ( módulos seguem junto)
```

### 9.4 Traefik — pontos críticos (validados no SCSI)

- **TLS wildcard** via Let's Encrypt **DNS-01 challenge com Cloudflare** (emite uma vez, cobre todos os subdomínios). Token lido de secret via `*_FILE`.
- **`forwardedHeaders.trustedIPs`** = faixas da Cloudflare (necessário p/ `X-Forwarded-*` correto).
- **Healthcheck do LB Traefik** deve incluir **`healthcheck.hostname=${DOMAIN}`** — sem isso o Traefik bate no IP da task (ex.: `10.0.x.x`) que não está no `ALLOWED_HOSTS` → `400 DisallowedHost`.
- **Basic auth** do dashboard: `htpasswd -nbB admin 'SENHA'` (hash com **um** `$`; via env, não duplicar).
- **Rate limit** no router do app (ex.: `average=100, burst=50`).
- **Endpoint `/health/`** isento de `SECURE_SSL_REDIRECT` (saúde interna do container/LB bate em http).

### 9.5 Django settings de produção (`DEBUG=False`)

- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` (TLS termina no Traefik)
- `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*`, `SECURE_CONTENT_TYPE_NOSNIFF`
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `X_FRAME_OPTIONS='DENY'`
- `CSRF_TRUSTED_ORIGINS` via `.env` (inclui `https://<dominio>`)
- WhiteNoise `CompressedStaticFilesStorage` para servir estáticos pelo app
- **Media protegida**: nunca mapear `MEDIA_URL` em `urls.py`; servir só via view autenticada (CSRF+sessão)

### 9.6 VPS Recomendada

- **Hostinger KVM 4** (4 vCPU, 8GB RAM, 200GB NVMe)
- Mínimo: KVM 2 (2 vCPU, 4GB RAM, 100GB NVMe)
- Cloudflare para DNS + CDN + proxy SSL (IPs reais ocultos)

### 9.7 Segurança do host

- Fail2ban (proteção brute force SSH)
- UFW (portas 22, 80, 443)
- SSH hardening (key only, disable root)
- Swap 4GB
- sysctl tuning para produção
- `daemon.json` Docker com log-rotation (max-size/max-file) e DNS config
- Imagens Docker não-rotuladas (`image prune`) em cron

### 9.8 CI/CD (recomendado)

- GitHub Actions: em push na `main` → `docker build` + `push` para GHCR (imagem única da plataforma com todos os módulos instalados)
- Na VPS: `docker stack deploy -c docker-stack.yml komotores_pcp` (pull da imagem nova)
- Healthcheck do `app` via `/health/` garante zero-downtime (replicas 2 + `order: start-first`)

---

## 10. Projetos de Referência

- **SCSI Imersão (padrão arquitetural de referência):** https://github.com/Mizael2025-hub/scsi_imersao_v1 — usar como modelo de: apps na raiz, `base/` (BaseModel + mixins + managers), `accounts.User` customizado por email, settings com `django-environ`, Celery autodiscover, `entrypoint.sh` com advisory lock, `docker-stack.yml` Swarm+Traefik.
- **SCSI** (Sistema de Corretora de Seguros): https://github.com/pycodebr/scsi
- **Finanpy:** https://github.com/pycodebr/finanpy
- **MentorIA:** https://mentoria.expert

---

## 11. Glossário

| Termo | Significado |
|-------|-------------|
| Plataforma | Infraestrutura fixa do repositório (core, base, accounts, shell, shared) — é a "base" sobre a quais módulos se instalam |
| Módulo | Pacote de domínio de negócio em `modules/<nome>/`, removível, que se apoia na plataforma |
| Manifest | Arquivo declarativo (`modules/<nome>/manifest.py`) com metadados do módulo: slug, label, menu, permissões, widgets de dashboard |
| Registry | Registro central (`modules/registry.py`) dos manifests, preenchido no `AppConfig.ready()` de cada módulo; lido pelo `shell` |
| Shell | App da plataforma que provê layout, navegação dinâmica e dashboard agregada (o "portal") |
| Shared | App da plataforma com cadastros cross-módulo (Setor, Operador, Turno, Máquina) |
| `shared` vs módulo | Cadastro usado por 2+ módulos → `shared`; usado por só 1 módulo → dentro do módulo |
| Permissão por módulo | `ModulePermission` (user × module_slug × role) — papel VÁLIDO dentro de um módulo; admin global always passa |
| Chumbo | Metal (Pb) usado na produção de baterias |
| Lingote | Peça de chumbo bruto (matéria-prima) |
| Lote | Conjunto de lingotes recebidos em uma mesma data |
| Monte | Pilha física de lingotes disposta em posição na grade |
| Grade | Layout 2D (colunas x linhas) organizando os montes no chão de fábrica |
| Liga | Composição química do chumbo (liga específica para cada tipo de bateria) |
| Borra | Resíduo/escória do chumbo após fusão (dross) |
| Estorno | Reversão de uma operação de saída/liberação |
| Split | Divisão de um monte em dois (movimentação parcial) |
| FIFO | First In, First Out — método de consumo que prioriza os montes mais antigos |

---

## 12. Guia: adicionar um novo módulo (ex.: "Óxido")

> Este guia documenta o **passo a passo canônico** para criar um novo módulo — prova de que a plataforma é realmente modular. Cada novo módulo segue exatamente estes passos, sem tocar na plataforma.

1. **Criar o pacote:** `modules/oxido/` com `__init__.py`, `apps.py`.
2. **Declarar o Manifest:** `modules/oxido/manifest.py` com `slug="oxido"`, label, ícone, `url_name="oxido:home"`, menu, `dashboard_widgets`.
3. **Registrar no ready():** em `OxidoConfig.ready()`, chamar `modules.registry.register(MANIFEST)`.
4. **Adicionar ao `INSTALLED_APPS`** (e sub-apps do módulo) no `core/settings.py` — na seção `MODULES` (variável `MODULES = ['chumbo', 'oxido']` opcional, p/ auto-includes).
5. **Montar as URLs:** `path('oxido/', include('modules.oxido.urls', namespace='oxido'))` em `core/urls.py` (ou auto-registro, ver §2.7).
6. **Models:** criar dentro do módulo; FKs só para `base`, `shared` ou o próprio módulo (**nunca** outro módulo).
7. **Permissões:** o admin global já acessa; para outros usuários, criar `ModulePermission(user, 'oxido', role)` via tela de gerenciamento.
8. **Dashboard:** contribuir com widgets listados no `dashboard_widgets` do manifest — aparecem na home agregada do `shell`.
9. **Migrations + seeds:** `makemigrations oxido_*` + seed próprio (pode ler `shared` se precisar de setores/operadores).
10. **Teste de removibilidade:** remover o módulo do `INSTALLED_APPS` + comentar o `include` de urls → plataforma deve voltar a rodar sem erros (valida que nenhuma referência cruzada foi criada por engano).

> **Anti-padrões a evitar:** (a) `shared` importar de um módulo → acoplamento da plataforma ao módulo. (b) Um módulo importar outro (`from modules.chumbo...` dentro de `modules.oxido`) → vira monólito disfarçado. (c) URL fixa no `shell` para um módulo → sempre use `url_name` e o registry.
