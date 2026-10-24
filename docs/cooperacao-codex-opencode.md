# Cooperação OpenCode × Codex

Plano operacional para concluir as fases A–G do INCARNATE com dois agentes.
O usuário é o único aprovador de merge, release e mudança de escopo. Este
documento complementa [roadmap-fases.md](roadmap-fases.md) e o PR #43.

## 1. Princípio

- **OpenCode:** trabalho pesado — arquitetura, código, testes, benchmark,
  depuração, performance, capturas e integração de fases.
- **Codex:** trabalho leve e delimitado — inventário, checklist, documentação,
  PR, verificação de artefatos, atualização de `CHANGELOG`/`ROADMAP`/`AI_USAGE`
  e revisão de texto. Codex não faz refatoração ampla nem implementa sistemas
  novos.
- **Usuário:** decide escopo, aprova telas/visual, fornece o teste Windows e
  autoriza merge/tag. Nenhum agente faz merge ou tag sem essa autorização.

## 2. Regras de ouro

1. **Um escritor por branch/worktree.** Nunca os dois no mesmo diretório.
2. Os worktrees `feat/ui-kit-c` e `feat/polimento-visual-d` pertencem ao
   OpenCode. Codex não deve editá-los, rebaseá-los nem fazer commit neles.
3. Codex usa worktrees próprios, por exemplo `/tmp/incarnate-cx-<fase>`, e
   branches `docs/...` ou `ci/...`, sempre a partir da `origin/main` atualizada.
4. Antes de começar: `git fetch`, `git status`, conferir a base e o PR #43.
5. Uma fase por vez. E pode ser intercalada por mexer quase só em JSON/testes;
   C e D não podem rodar em paralelo, pois compartilham HUD, tema e telas.
6. OpenCode escreve código e testes. Codex escreve documentação e checklists
   **depois** do congelamento do código, salvo tarefa documental independente.
7. Se Codex achar um bug de código, ele **não corrige**: registra no handoff e
   devolve para OpenCode.
8. Não tocar na main local, no checkout original, em branches antigas, tags ou
   worktrees existentes. Sem force push, `reset --hard` ou remoção.
9. Cada entrega tem PR em rascunho. Merge e tag só depois de aprovação
   explícita do usuário; tag de segurança na `origin/main` antes do merge.
10. O `docs/roadmap-fases.md` e o PR #43 são a memória. Divergência de plano se
    resolve no PR, não por iniciativa isolada.

## 3. Fluxo de uma fase

```text
PLANO (OpenCode) → APROVAÇÃO (usuário) → CÓDIGO (OpenCode)
→ CONGELADO (SHA) → VERIFICAÇÃO + DOCS (Codex)
→ REVISÃO (OpenCode) → APROVAÇÃO VISUAL (usuário)
→ TAG DE SEGURANÇA → MERGE (OpenCode) → PÓS-MERGE (Codex)
```

- **CÓDIGO:** OpenCode mantém a branch da fase. Codex só observa.
- **CONGELADO:** OpenCode informa SHA, arquivos, comandos e pendências.
- **VERIFICAÇÃO + DOCS:** Codex roda os comandos indicados, atualiza docs e
  devolve um relatório curto. Não altera código.
- **REVISÃO:** OpenCode confere diff, testes e documentação. Corrige o que for
  de código; devolve o que for de texto.
- **PÓS-MERGE:** Codex atualiza `ROADMAP.md`/`AI_USAGE.md` se ainda faltar algo.

### Handoff OpenCode → Codex

```text
ESTADO: CONGELADO
FASE: <A–G>
BRANCH: <branch>
SHA: <sha>
BASE: <origin/main no momento do rebase>
ARQUIVOS DE CÓDIGO: <lista>
ARQUIVOS DE DOCS PARA CODEX: <lista>
COMANDOS: <testes/ruff/benchmark já executados>
RESULTADOS: <números>
PENDÊNCIAS: <decisões, riscos, links>
NÃO TOCAR: <worktrees/arquivos>
```

### Handoff Codex → OpenCode

```text
ESTADO: VERIFICADO / FALHOU
FASE: <A–G>
BRANCH: <branch>
SHA: <sha>
DOCS ALTERADOS: <lista>
COMANDOS EXECUTADOS: <lista>
RESULTADO: <resumo curto>
DÚVIDAS: <perguntas objetivas>
AÇÃO ESPERADA: <revisar / corrigir / aprovar>
```

## 4. Divisão por fase

| Fase | Dono da implementação | OpenCode (pesado) | Codex (leve) | Aprovação |
| --- | --- | --- | --- | --- |
| A — release 1.8.0 | Codex, com revisão do OpenCode | Resolver conflito técnico da PR #36; conferir workflow, hashes e tag; revisar release | Checklist, README, docs de release, `CHANGELOG`/`AI_USAGE`, corpo do PR, conferir artefatos | Usuário testa Windows e autoriza tag |
| B — B4 + aceitação | OpenCode | Sons/parallax/animações do menu, testes, benchmark, capturas | Auditoria B1–B3, checklist das 8 combinações, docs, changelog | Usuário aprova etapa 4 |
| C — kit de UI | OpenCode | Componentes, piloto, migração das telas, `menu.py`, testes, capturas | Inventário/matriz de telas em lotes, `docs/ui-kit.md`, changelog, PR | Usuário aprova tela-piloto |
| D — visual residual | OpenCode | HUD, fundos, ícones, sprites, sequências, contraste, performance, testes | Checklist visual, índice de capturas, `docs/visual`, changelog | Usuário aprova cada etapa |
| E — capítulos 3–6 | OpenCode | JSON, gatilhos, testes, minibosses, continuidade | Sumários, léxico, checklist de revelações, docs, changelog | Usuário revisa cada capítulo |
| F — mundo aberto | OpenCode | Design técnico, câmera, chunks, save, protótipo, performance, testes | Registro de decisões, checklist, índice de GIFs, docs, PR | Usuário aprova design, câmera/fundo e protótipo |
| G — assinatura visual | OpenCode | Estilos, shaders/fallback, nave, transições, contraste, testes | Referências de estilo, registro de licenças, docs, changelog | Usuário aprova 2 dimensões + nave |

### Regra de arquivos

- **OpenCode:** `src/`, `tests/`, `assets/`, `images/`, capturas/GIFs, scripts de
  benchmark e qualquer correção de código.
- **Codex:** `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `AI_USAGE.md`, `docs/`
  (exceto `docs/roadmap-fases.md`), corpo de PR e checklists.
- Se um arquivo de doc precisar mudar durante o código, OpenCode registra a nota
  no handoff e Codex aplica depois do congelamento.
- Nunca os dois editam `CHANGELOG.md`, `ROADMAP.md` ou `AI_USAGE.md` ao mesmo
  tempo.

## 5. O que pode rodar em paralelo

Seguro:
- Codex documenta/verifica uma fase **congelada** enquanto OpenCode prepara o
  plano da próxima (sem código).
- Depois de B, capítulos de E podem ser preparados em branches separados,
  porque o risco de conflito é baixo.
- Codex atualiza docs pós-merge enquanto OpenCode começa a leitura da fase
  seguinte.

Inseguro:
- C e D simultâneos: HUD, tema, layout e telas.
- F e G simultâneos: cenários, sprites e renderização.
- Dois agentes na mesma fase de código.
- Merge de fase seguinte antes da anterior estar aprovada.

## 6. Orçamento de tokens do Codex

Toda tarefa para Codex deve caber em uma destas formas:

1. **Docs:** no máximo 3–5 arquivos e um diff pequeno.
2. **Verificação:** comandos exatos e resultado esperado; sem explorar o repo.
3. **Inventário:** uma lista fechada de telas/arquivos, em lotes.
4. **PR:** usar o handoff do OpenCode; não reescrever o plano.

Regras:
- Não fazer varredura ampla se o caminho já foi indicado.
- Não rodar benchmark completo; OpenCode fornece os números.
- Não repetir a suíte completa mais de uma vez por handoff.
- Não gerar código extenso, refatorar ou “melhorar” arquitetura.
- Devolver relatório curto, com comandos e falhas literais.
- Em dúvida, parar e perguntar ao usuário; não inventar escopo.

## 7. Estado após integração dos PRs #36–#42

1. A integração técnica da Fase A (PR #36) está na main. O teste manual dos
   binários no Windows ainda está pendente; não criar tag ou release final até
   o usuário testar e aprovar.
2. B2 (PR #42) está integrado. B4 e a Fase C continuam dependendo da aprovação
   e dos testes do usuário; não iniciar F1 antes de A, B e C.
3. O PR #43 atualiza o Passo 0, registra o estado posterior aos merges e as
   decisões confirmadas do mundo aberto. O PR #34 permanece fechado e
   substituído pelo #43.
4. Branches de roteiro E e design F continuam separadas e não integradas.
   Usar o handoff do OpenCode e trabalhar uma tarefa por branch.

## 8. Critério para considerar a cooperação saudável

- Nenhum commit perdido por dois agentes no mesmo worktree.
- Cada fase tem um único dono de código e um único dono de docs por vez.
- Todo merge tem aprovação explícita, tag de segurança e PR.
- Codex nunca precisa “descobrir” o estado: recebe SHA, lista de arquivos e
  comandos no handoff.
- OpenCode não gasta tempo com documentação repetitiva; Codex não gasta tokens
  com arquitetura ou debugging pesado.
