# AGENTS.md — Plataforma PCP (Módulo: Controle de Chumbo)

> Lido automaticamente pelo OpenCode ao abrir o projeto.
> Define stack, workflow e regras que a IA deve seguir aqui.

---

## Projeto (leia o PRD.md primeiro)

Este repositório é a **Plataforma PCP da fábrica** (chão de fábrica digital,
Python/Django). O **Controle de Chumbo** é o primeiro **módulo** instalado
sobre ela. Módulos futuros (Óxido, Borra, Qualidade, Manutenção...) são
adicionados sem alterar a plataforma.

- **Fonte da verdade:** `PRD.md` na raiz — leia antes de qualquer tarefa de código.
- **Análise do legado:** `ANALISE_sistema_antigo.md` (21 bugs do sistema Next.js/Dexie/Supabase).
- **Regras anti-regressão:** ARC-01 a ARC-20, definidas no PRD §6.9. Cada
  sprint cita as ARCs que cobre; os testes são nomeados `test_arcNN_*`.

---

## Stack (use SOMENTE estas)

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.13+ |
| Web | Django 5.x/6.x (`django-admin startproject core .` já feito) |
| ORM/BD | PostgreSQL 16+ + `psycopg[binary]` |
| IA | LangChain + LangGraph |
| Filas | Celery + RabbitMQ (Worker, Beat) + Redis (result/cache) |
| Agendamento Celery | `django-celery-beat` + `django-celery-results` + `dj-celery-panel` |
| Settings/env | `django-environ` |
| Staticfiles prod | WhiteNoise (compresso) |
| WSGI | Gunicorn (gthread, 2 threads) |
| Dev | Docker Compose |
| Produção | Docker Swarm + Traefik (Let's Encrypt DNS-01 via Cloudflare) |
| Registro de imagens | GHCR |
| Frontend | Django Templates + HTMX + Alpine.js + Design System extraído |
| PWA | manifest.json + Service Worker (Workbox) + IndexedDB outbox + Background Sync |
| PDF | Reportlab |

---

## Workflow de IA Assistida (OBRIGATÓRIO — 5 etapas)

1. Prompt bruto → Prompt refinado
2. Prompt refinado → **PRD.md** (já entregue)
3. PRD.md → Start Template (em andamento)
4. Start Template → Sprint (uma por vez, do PRD §8)
5. Sprint → Review, Correções e Commit

**Status atual:** etapa 3 (Start Template) parcial — só rodou
`django-admin startproject core .`. Faltam: `.env`/`.env.example`,
`django-environ`, `requirements.txt` completo, `settings.py` ajustado
(pt-BR, America/Sao_Paulo, ALLOWED_HOSTS, apps da plataforma), Docker
Compose, design system. Depois segue para a **Sprint 1 (Plataforma)**.

---

## Regras da IA neste projeto

### Antes de codar
- Leia o `PRD.md` — ele é a especificação (SDD).
- Confirme a sprint/seção do PRD antes de implementar.
- Usuário **não é programador** — seja direto, resumido, e peça confirmação
  antes de ações destrutivas ou comandos longos.

### Estrutura (modularidade — regra de ouro)
- Apps na raiz, sem pasta `apps/`.
- **Plataforma:** `core`, `base`, `accounts`, `shell`, `shared` — fixos.
- **Módulos:** em `modules/<nome>/` (ex.: `modules/chumbo/`).
- Um módulo **NUNCA** importa outro módulo. FKs só para `base`, `shared`
  ou o próprio módulo. `shared` **nunca** importa de um módulo.
- Cada módulo declara `manifest.py` e se registra no `modules/registry.py`
  via `AppConfig.ready()`.
- Custom `User` (`accounts.User`, login por email) — `AUTH_USER_MODEL`
  fixado **antes do primeiro migrate**.

### Convenções de código
- `.venv` sempre — nunca instale no Python global.
- Código em **inglês** (models, fields, apps, views); UI em **pt-BR**.
- `DecimalField` para kg (nunca `FloatField`); `PositiveIntegerField` p/ barras.
- Timestamps UTC, exibidos em America/Sao_Paulo; datas dd/MM/yyyy.
- Soft delete (`is_active`) em cadastros; nunca exclusão física de master.
- Signals em `signals.py`, ligados no `AppConfig.ready()` (nunca em `models.py`).
- Views finas (CBV), lógica em `services.py`.
- Sem comentários no código, salvo quando pedido.

### Anti-regressão (ARC-01..20 — ver PRD §6.9)
- Status CONSUMED = `barras<=0 OU peso<=EPSILON` (||, nunca &&); zera residual.
- Operações em monte em `transaction.atomic()` + `select_for_update()`.
- Grade 2D mobile-first (min-cell 40px, nunca colunas fixas largas).
- Reset por módulo (nunca global). Sync offline em `base/sync/`.

### Git / Commits
- Commit frequente, mas **só commit/push quando o usuário pedir explicitamente**.
- Git é do usuário — não terceirize o versionamento.

### Deploy
- Serviços: app, PostgreSQL, Celery Worker, Celery Beat, RabbitMQ, Redis, Traefik.
- Redes overlay: `traefik_public`, `komotores_pcp_internal`, `komotores_pcp_egress`.
- Imagem única no GHCR; SSL via Traefik + Let's Encrypt (DNS-01 Cloudflare).

---

## Documentação do curso (referência)

```
C:\Users\Usuario\OneDrive\02-PCP KOMOTORS\sistemas\Documentação notion v1.0\
├── index.md                    ← índice central (comece aqui)
├── docs\
│   ├── 01-tech-stack.md        ← stack detalhada
│   ├── 02-workflow.md          ← 5 etapas + SDD + design system
│   ├── 03-setup-local.md       ← setup local (WSL, Python, Docker)
│   ├── 04-deploy.md            ← deploy em produção
│   └── 05-boas-praticas.md     ← dicas e macetes
└── (aulas originais preservadas)
```

## Projetos de referência
- SCSI Imersão (padrão arquitetural de referência): https://github.com/Mizael2025-hub/scsi_imersao_v1
- SCSI: https://github.com/pycodebr/scsi
- Finanpy: https://github.com/pycodebr/finanpy

## Modelos de IA recomendados
- GLM-5.2, MiniMax M3, Kimi K2.7 Code (via OpenCode Go)
- GPT-5.5 (via ChatGPT Plus)
- Opus 4.8 (via Claude Code Max)
- DeepSeek V4 Flash / Pro (alto limite, via OpenCode Go)
