---
name: ia-builders-workflow
description: Use when building, planning, or deploying this Python/Django project with AI assistance. Covers the 5-step "Workflow de IA Assistida" method (PycodeBR) — raw prompt, PRD.md, start template, sprint, review/commit. Also use when discussing the stack (Django, LangChain/LangGraph, PostgreSQL, Celery, RabbitMQ, Docker Swarm, Traefik, Cloudflare) or needing spec-driven development guidance.
---

# Skill: Workflow de IA Assistida (IA Builders — PycodeBR)

Este skill codifica o método "Workflow de IA Assistida" do curso Imersão IA
Builders. Aplica-se a projetos Python/Django (não usar em Node/Go/etc.).

Referência completa: `C:\Users\Usuario\OneDrive\02-PCP KOMOTORS\sistemas\Documentação notion v1.0\index.md`
e subpastas `docs/` (temático) e aulas originais.

---

## 1. A stack (use SOMENTE estes)

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.13+ |
| Web | Django (`django-admin startproject core .`) |
| IA/agentes | LangChain + LangGraph |
| Banco | PostgreSQL |
| Filas | Celery + RabbitMQ (Worker, Beat) |
| Dev | Docker + Docker Compose |
| Produção | Docker Swarm |
| Proxy/SSL | Traefik + Let's Encrypt |
| DNS/CDN | Cloudflare |

Sempre use `.venv`. Nunca instale no Python global. `requirements.txt` via
`pip freeze`. `.env` para variáveis (django-environ, dj-database-url) e
`.env` nunca vai para o Git.

---

## 2. Workflow (OBRIGATÓRIO — 5 etapas)

```
1.Prompt bruto -> 2.PRD.md -> 3.Start Template -> 4.Sprint -> 5.Review/Commit
```

1. **Prompt bruto → Prompt refinado.** Detalhar tudo: requisitos
   funcionais e não funcionais, tech specs, jornadas do usuário. Pedir a IA
   para refinar. Esta etapa demanda a maior parte do tempo.
2. **Prompt refinado → PRD.md.** IA gera o Product Requirements Document.
   É a base do Spec-Driven Development (SDD).
3. **PRD.md → Start Template.** Criar projeto, venv, Django, adicionar o
   PRD.md na raiz, extrair e adicionar o design system em `design_system/refs/`.
4. **Start Template → Sprint.** Executar UMA sprint do PRD por vez. Acompanhar
   de perto a IA.
5. **Sprint → Review, Correções e Commit.** Revisar código, ajustar (manual
   ou IA), validar, commit e push. Repetir para a próxima sprint.

Se o usuário ainda não tem `PRD.md`, pare e ajude a criar um antes de codar.

---

## 3. Regras de conduta

- **SDD sempre:** especificação antes de código.
- **Não commit/push** sem o usuário pedir explicitamente.
- **Git é do usuário:** não terceirize o versionamento para a IA.
- **Sem comentários** no código, salvo quando o usuário pedir.
- **Siga o idioma Django:** baterias inclusas (admin, ORM, auth, forms).
- Usuário não é programador — seja direto e resumido.

---

## 4. Deploy (arquitetura)

A arquitetura de deploy já começa no prompt bruto. Deixe explícito:

- Serviços: app Django, PostgreSQL, Celery Worker, Celery Beat, RabbitMQ, Traefik
- Redes overlay: `traefik_public` (pública), `<projeto>_internal`
  (isolada), `<projeto>_egress` (saída para internet)
- VPS: Ubuntu LTS, mínimo 2 vCPU / 8 GB RAM
- Hardening: Fail2ban, UFW (22/80/443), swap 4 GB, sysctl tuning
- Imagens: GitHub Container Registry (GHCR)
- SSL: Traefik + Let's Encrypt challenge DNS-01 com Cloudflare API token
  (docker secret: `CLOUDFLARE_DNS_API_TOKEN`)
- Deploy: `docker stack deploy -c docker-stack.yml <projeto>`
- Seed: Django Command `seed_demo --force`

Detalhes passo a passo: `...\Documentação notion v1.0\docs\04-deploy.md`.

---

## 5. Macetes rápidos

- Quanto mais detalhe no prompt, melhor o resultado (sem preguiça de escrever).
- Tenha pelo menos 2 provedores de IA configurados.
- Extrair design system de sites de referência (Aura Build, Linear) → aparência profissional.
- Commit frequente, mas só quando o usuário pedir.

---

## 6. Quando NÃO usar este skill

- Projetos que não usem Python/Django (Node, Go, etc.).
- Configuração do próprio OpenCode (use o skill `customize-opencode`).
- Tarefas puramente informativas sem relação com desenvolvimento de software.
