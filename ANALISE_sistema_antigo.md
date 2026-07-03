# Análise Completa — Sistema Controle de Chumbo

**Data:** 19/06/2026
**Projeto:** controle_chumbo (Next.js + Dexie + Supabase)
**Tipo:** Análise estática de código-fonte

---

## Legenda

| Prioridade | Significado |
|-----------|-------------|
| 🔴 **ALTA** | Erro de lógica que pode corromper dados ou quebrar fluxo crítico |
| 🟡 **MÉDIA** | Problema funcional que causa inconsistência ou má experiência |
| 🔵 **BAIXA** | Questão de UX, legibilidade ou robustez |
| 🟢 **OPCIONAL** | Melhoria ou sugestão |

---

## 1. Erros de Lógica (Obrigatório)

### 🔴 #1 — Status CONSUMED com peso residual

**Arquivo:** `lib/applyConsumption.ts:89`
```ts
const consumed = nextBars <= 0 && nextWeight <= 0;
await db.leadPiles.update(pile.id, {
  current_weight: consumed ? 0 : nextWeight,
  status: consumed ? "CONSUMED" : pile.status === "RESERVED" ? "RESERVED" : "PARTIAL",
});
```

**Problema:** Se `nextBars = 0` mas `nextWeight = 0.002` (peso residual de arredondamento), a condição `&&` falha, o status muda para `PARTIAL` em vez de `CONSUMED`, e o peso residual nunca é zerado. Isso faz o monte acumular peso "fantasma" que não pode ser consumido.

**Correção:** Usar `||` em vez de `&&`, ou `nextBars <= 0 || nextWeight <= 0`.

---

### 🔴 #2 — Estorno pode criar estado inconsistente

**Arquivo:** `lib/reverseReleaseTransaction.ts:36`
```ts
if (nw === 0 && nb === 0) {
  status = "CONSUMED";
}
```

**Problema:** Mesmo problema do item 1 mas no sentido oposto. Se as barras voltam a zero mas sobra peso residual, o monte não volta para CONSUMED, pode ficar num estado sem barras mas com peso.

---

### 🟡 #3 — Falta validação de existência da liga ao criar lote

**Arquivo:** `lib/createBatchFromGrid.ts`

**Problema:** A função consulta `db.leadAlloys.get(alloy_id)` para validar a liga, mas se o registro for excluído entre essa validação e a transação, o lote é criado com `alloy_id` inválido, gerando órfão.

---

### 🟡 #4 — Edição de consumo sem feedback de erro no load inicial

**Arquivo:** `components/ConsumptionView.tsx:148-152`

**Problema:** Ao abrir um apontamento para edição vindo do relatório, `loadEntry` busca os dados no DB mas não trata erro. Se o registro for deletado entre a consulta e o carregamento, o form fica preenchido parcialmente sem notificar o usuário.

---

### 🟡 #5 — Fila de sync individual por pile após consumo

**Arquivo:** `lib/consumptionEntryCrud.ts:162-166`
```ts
for (const p of planned) {
  const pile = await db.leadPiles.get(p.pile_id);
  if (pile) await enqueueUpsert("leadPiles", pile);
}
```

**Problema:** Caso um `enqueueUpsert` falhe, o estado entre servidor e local fica inconsistente. Todo bloco deveria estar numa transação ou ter rollback.

---

### 🟡 #6 — Liberação parcial: kg não recalcula quando barras mudam após kg manual

**Arquivo:** `components/ReleaseModal.tsx:268-282`

**Problema:** Se o usuário marca "parcial", digita as barras (kg auto-preenche), depois altera o kg manualmente (`kgTouched = true`), e então altera as barras de novo, o kg NÃO recalcula (porque `kgTouched` já é `true`). Pode gerar divergência entre kg barra.

---

### 🟡 #7 — Reserva e devolução: campos órfãos

**Arquivo:** `lib/returnPileToWarehouse.ts:22`
```ts
await db.leadPiles.update(pileId, {
  storage_location: "warehouse",
  sector_moved_at: null,
});
```

**Problema:** Ao devolver ao almoxarifado, `reserved_sector_id`, `reserved_for`, `reserved_at` permanecem no monte. A intenção é manter a reserva, mas não há validação se a reserva original ainda existe no sistema.

---

### 🟡 #8 — Sessão expirada pode tentar sync ao voltar online

**Arquivo:** `components/SyncProvider.tsx:67-76`

**Problema:** Ao ficar online, `onOnline` tenta `flushOutbox` sem verificar se a sessão expirou (usa `getSyncPausedForAuth()` mas o fluxo `resetOutboxForReconnect` roda antes de verificar).

---

## 2. Problemas de Sincronização (Sync)

### 🟡 #9 — LWW com resolução de milissegundos

**Arquivo:** `lib/syncEngine.ts`

**Problema:** A estratégia Last-Writer-Wins usa `updated_at` com precisão de ms. Se dois dispositivos criarem/modificarem o mesmo registro simultaneamente (offline), o último `updated_at` vence, mas pode perder dados do outro.

**Sugestão:** Documentar essa limitação para o usuário, ou implementar CRDT para campos críticos.

---

### 🟡 #10 — Estado global `pausedForAuth` compartilhado entre abas

**Arquivo:** `lib/syncAuthPause.ts`

**Problema:** `pausedForAuth` e `listeners` são variáveis de módulo (singleton). Se o usuário abrir duas abas com sessões diferentes, uma aba pode pausar o sync da outra.

---

### 🟡 #11 — Pull delta perde registros no mesmo ms do cursor

**Arquivo:** `lib/syncEngine.ts:956-958`
```ts
query = query.gt("updated_at", lastSyncTimestamp);
```

**Problema:** Usar `gt` (greater than) em vez de `gte` (greater or equal) significa que registros com `updated_at` idêntico ao cursor são perdidos até o próximo pull completo.

---

## 3. Problemas de Interface Mobile / UX

### 🔵 #12 — Grade fixa de 7 colunas em mobile estreito

**Arquivo:** `components/PileGrid.tsx:381`
```css
[grid-template-columns:repeat(7,96px)]
```

**Problema:** Em telas < 375px (ex.: iPhone SE), 7 × 96px = 672px, exigindo scroll horizontal mesmo para um único lote. Isso prejudica severamente a usabilidade mobile.

---

### 🔵 #13 — Dashboard limita a 6 ligas

**Arquivo:** `components/AlloyDashboard.tsx:33`
```ts
rows.slice(0, 6)
```

**Problema:** O dashboard sempre mostra apenas as 6 primeiras ligas (ordenadas por nome). Se houver mais, o usuário precisa navegar manualmente até "Estoque" para ver as demais. Pode gerar confusão.

---

### 🔵 #14 — Texto instrutivo longo na grade

**Arquivo:** `components/PileGrid.tsx:376-378`

**Problema:** A descrição "Toque no monte para selecionar. No Menu: reservar, levar ao setor (azul RES), devolver (amarelo SET), liberar e outras ações." ocupa 3+ linhas em mobile e usa siglas (RES, SET) que não são explicadas.

---

### 🔵 #15 — Botão "+" central pode sobrepor gestos nativos

**Arquivo:** `components/AppBottomNav.tsx:131-137`

**Problema:** O botão "+" flutuante com `-mt-6` fica sobre a barra de navegação do sistema em alguns dispositivos Android, podendo causar toques fantasmas.

---

## 4. Melhorias OPCIONAIS

### 🟢 #16 — Duplicação de `flushOutbox`

**Arquivo:** `lib/syncEngine.ts:1193`
```ts
await flushOutbox(supabase, ownerId, callbacks);
await flushOutbox(supabase, ownerId, callbacks);
```

Chamado 2x seguidas em `runManualCloudReconciliation`. Parece intencional (drenar fila com batch de 50), mas sem documentação parece duplicação. Adicionar comentário ou loop.

---

### 🟢 #17 — Acesso early ao IndexedDB não comprovado

**Arquivo:** `components/LeadApp.tsx:244-246`
```ts
globalThis.indexedDB;
```

**Problema:** Acesso ao indexedDB para forçar inicialização do WebKit não tem base científica comprovada em nenhuma referência. Pode ser removido.

---

### 🟢 #18 — Sem filtro por modelo de produto no relatório de consumo

**Arquivo:** `lib/reportFilterRules.ts`

**Problema:** O campo `product_model_id` existe na entidade `LeadConsumptionEntry` e está no schema do Dexie, mas não há filtro por modelo no relatório de consumo.

---

### 🟢 #19 — Lote sem saldo pode ser selecionado no consumo

**Arquivo:** `components/ConsumptionView.tsx`

**Problema:** O select de "Lote de chumbo" lista todos os lotes da liga, mesmo aqueles que não têm montes disponíveis no setor. O usuário pode selecionar um lote sem saldo e receber erro ao salvar.

---

### 🟢 #20 — `kgPerBarFromPile` retorna 0 silenciosamente

**Arquivo:** `lib/pileWeight.ts:2-3`
```ts
if (!Number.isFinite(weight) || !Number.isFinite(bars) || bars <= 0) return 0;
```

**Problema:** Retorna 0 em vez de lançar erro ou log, o que pode mascarar divisões por zero em cascata.

---

### 🟢 #21 — Realtime escuta eventos internos desnecessários

**Arquivo:** `lib/syncEngine.ts:1277-1282`

**Problema:** O canal Realtime escuta todas as tabelas, inclusive `leadPileEvents` que contém movimentações internas (MOVED_TO_SECTOR, MOVED_BACK_TO_WAREHOUSE). Esses eventos são gerados localmente e enviados via outbox, então recebê-los de volta pelo Realtime é redundante.

---

## 5. Arquivos Não Analisados

Estes arquivos existem no projeto mas não foram lidos durante a análise:

| Arquivo | Risco |
|---------|-------|
| `components/PileReleaseSheet.tsx` | Médio — componente de release info |
| `components/ReportFilterSheet.tsx` | Médio — filtros do relatório |
| `components/ErrorBanner.tsx` | Baixo — exibição de erros |
| `components/BatchEntryGrid.tsx` | Médio — grade de entrada de lote |
| `components/AlloyColorPicker.tsx` | Baixo |
| `components/CloudSyncButton.tsx` | Baixo |
| `components/CloudSyncPanel.tsx` | Médio |
| `components/ConfigScreenShell.tsx` | Baixo |
| `components/SyncStatusIndicator.tsx` | Baixo |
| `app/globals.css` | Médio — variáveis CSS |
| `hooks/useDesktopLayout.ts` | Baixo |
| `supabase/migrations/` | Alto — estrutura do banco |
| `app/error.tsx` | Baixo |
| `app/global-error.tsx` | Baixo |

---

## 6. Avaliação Geral

### Pontos Fortes

- ✅ Arquitetura offline-first sólida com Dexie + fila de sync (outbox)
- ✅ Transações Dexie para operações críticas (consumo, liberação, reserva)
- ✅ Separação clara entre lógica de negócio (`lib/`) e UI (`components/`)
- ✅ Tratamento de erros de rede e autenticação bem estruturado
- ✅ Suporte PWA (manifest, apple-touch-icon, offline)
- ✅ Cobertura de safe-area-inset-bottom para notches

### Riscos Identificados

| Risco | Impacto | Probabilidade |
|-------|---------|---------------|
| Peso residual fantasma (item 1) | **Dados incorretos** | Alta |
| Conflito de sync entre dispositivos | **Perda de dados** | Média |
| Grade 7 colunas em telas pequenas | **Inusitável em mobile** | Alta |
| Sessão expirada sem feedback claro | **Dados não sincronizados** | Média |

### Recomendação

Corrigir itens **#1** e **#2** antes de qualquer uso em produção. Em seguida, priorizar **#3**, **#6**, **#9**, **#12** para garantir consistência dos dados e usabilidade mobile.

---

## Checklist de Implantação

- [ ] Corrigir condição CONSUMED em `applyConsumption.ts`
- [ ] Corrigir condição CONSUMED em `reverseReleaseTransaction.ts`
- [ ] Validar consistência entre kg/barras em liberações parciais
- [ ] Ajustar grade para responsividade em telas < 400px
- [ ] Verificar se o `manifest.webmanifest` existe em `public/`
- [ ] Configurar variáveis de ambiente `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] Rodar `npm run build` para verificar erros de compilação
- [ ] Testar fluxo completo: cadastro → entrada → reserva → setor → consumo → relatório
