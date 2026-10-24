# Plano de fases do INCARNATE — Passo 0

Levantamento feito em 24/10/2026 sobre `origin/main` em `63ae5dc` (merge do
PR #42). Este documento é uma **proposta para aprovação**. Nenhuma fase de
implementação foi iniciada por ele. O [ROADMAP](../ROADMAP.md) continua sendo a
memória do projeto e deve ser atualizado a cada integração, junto de
`CHANGELOG.md` e `AI_USAGE.md`.

## 1. Inventário

### 1.1 Repositório, branches e tags

- `origin/main`: `63ae5dc` (PR #42 integrado).
- `main` local: `bebe716`, 18 commits atrás de `origin/main`; não foi tocada.
- Checkout original: branch `fix/build-limpa-moedas-tiros` em `20bf828`, com 8
  entradas locais (5 arquivos modificados e 3 documentos não rastreados). Deve
  permanecer intocado.
- 38 branches remotas, 30 branches locais, 36 worktrees registrados (incluindo
  este novo) e 16 worktrees marcados como *prunable*. Nenhum será removido sem
  pedido explícito.
- 8 tags locais/remotas. A `v1.8.0-rc1` aponta para `f383926`; **não existe
  `v1.8.0`**. O `pyproject.toml` já declara `1.8.0`, mas a release oficial
  continua pendente.

### 1.2 PRs relevantes

| PR | Situação | Observação |
| --- | --- | --- |
| #29, #30 | integrados | LICENSE/OFL e limpeza Ruff antiga já estão na main. |
| #31, #32, #33 | integrados | Menu original, fallback gráfico e build limpa. |
| #34 | fechado | Plano de fases anterior; não foi integrado. Este documento o substitui. |
| #35, #38, #39 | fechados | Auditoria da RC, proposta SemVer e capítulo 3 como documento. |
| #36 | aberto | Promoção de binários da 1.8.0; antes estava em conflito com a main. |
| #37 | integrado | Nomes de perfil com apóstrofo e regressão de nomes legados. |
| #40 | integrado | Capítulo 2 no JSON de produção. |
| #41 | integrado | Regras operacionais no AGENTS/AI_USAGE. |
| #42 | integrado | Fechamento da navegação B2 dos hubs do menu. |

### 1.3 O que já está na main

| Fase | Estado real |
| --- | --- |
| A | Licença MIT, OFL, Ruff antigo e nomes de perfil resolvidos. Falta a decisão de release/binários da 1.8.0. |
| B | B1 (correções visuais), B2 (navegação/hubs) e B3 (cartão, resumos, selos, 4:3, remoção de telemetria falsa) estão integrados. **B4 (sons, parallax e animações finais do menu) não está.** |
| C | Nenhuma migração do kit de UI está integrada. Existe apenas um piloto local não commitado. |
| D | HUD/tipografia, fundos por dimensão e contornos das etapas anteriores já entraram nas versões 1.6–1.8. O restante é auditoria e polimento residual; D1/D2 existem apenas em worktree. |
| E | Capítulo 2 está integrado. Capítulos 3–6 e falas de minibosses existem numa branch antiga, não integrada. |
| F | Existe um documento de design não integrado; nenhum código de mundo aberto foi iniciado. |
| G | Não há trabalho iniciado. |

### 1.4 Trabalho não integrado que não pode ser confundido com fase concluída

| Fase | Branch/worktree | Base | Estado |
| --- | --- | --- | --- |
| B4 | `feat/menu-sons-parallax` em `/tmp/incarnate-b4-menu` | `cbe4702` | Sem commits; branch vazia. |
| C | `feat/ui-kit-c` em `/tmp/incarnate-c-kit` | `cbe4702` | Piloto de Recordes, componentes e capturas **sem commit**. Relato da sessão: 656 testes, 1 skip. Precisa de rebase e auditoria. |
| D | `feat/polimento-visual-d` em `/tmp/incarnate-d-polimento` | `cbe4702` | D1 + D2 **sem commit**, com testes, docs e capturas. O `AI_USAGE` registra 648 testes/1 skip; neste inventário, 27 testes direcionados de HUD/fundos passaram. Ruff não está instalado no ambiente atual. |
| E | `feat/roteiro-capitulos-3-6` | `cbe4702` | Um commit com capítulos 3–6 e testes; 14 commits atrás da main e sem o capítulo 2 no histórico. |
| F | `docs/design-mundo-aberto` | `cbe4702` | Documento de design com decisões confirmadas; 14 commits atrás da main e sem PR aberto. |

As branches B4, C, D, E e F foram criadas sobre `cbe4702` e estão defasadas.
Nenhuma deve ser integrada diretamente sem rebase, revisão e novos testes.

## 2. Correções em relação ao pedido e ao ROADMAP

1. **Fase A:** LICENSE, avisos OFL, Ruff antigo e a regra de apóstrofo já foram
   integrados. Restam release, binários, hashes e decisão sobre a RC.
2. **Fase B:** B1–B3 já estão na main; não reimplementar. A etapa 4 continua
   pendente. O pedido de "capturas antes/depois" da etapa 3 já tem registro no
   `AI_USAGE`, mas a aprovação visual continua sendo do usuário.
3. **Fase C:** o kit ainda não existe na main. O piloto local de Recordes pode
   ser reaproveitado, mas não conta como fase concluída.
4. **Fase D:** HUD/tipografia, fundos e contornos antigos já foram entregues.
   D deve auditar o que falta, não refazer as etapas 1–5.
5. **Fase E:** o capítulo 2 já está no JSON de produção. O trabalho começa no
   capítulo 3; a branch 3–6 atual precisa ser dividida por capítulo.
6. **Fase F:** o design já foi escrito e as decisões principais estão
   confirmadas, mas o documento não está na main. Nenhum código pode começar
   antes da aprovação do design e da fase E.
7. **Versão:** `pyproject.toml` está em 1.8.0, mas a tag final não existe. A
   main atual contém mudanças posteriores à RC; isso impede prometer ao mesmo
   tempo "binários testados da RC" e "todo o conteúdo atual da main".

## 3. Ordem proposta e dependências

Ordem padrão: **A → B → C → D → E → F → G**.

| Ordem | Unidade | Dependência / parada | Risco e conflito | Versão se a ordem for mantida |
| --- | --- | --- | --- | --- |
| A | Fechamento da 1.8.0 | Resultado Windows; decisão RC antiga × novo build; aprovação explícita | Alto: tag, binários, hashes e main adiantada | 1.8.0 |
| B | B4 e aceitação final do menu | A integrada; B1–B3 já validados; parada visual da etapa 4 | Médio/alto com C/D/F em `menu.py`, tema e layout | 1.9.0 |
| C | Kit de UI e migração das telas | B integrada; aprovar tela-piloto antes das demais | Alto com B/D/F: menu, componentes, HUD e navegação | 1.10.0 |
| D | Polimento visual residual | C integrada; auditar D1/D2; decidir HUD na resolução final | Alto com C/G/F: HUD, fontes, cenários, sprites e cache | 1.11.0 |
| E | Capítulos 3–6 e final | A/B integradas; capítulo 3 aprovado; F depois | Baixo/médio: JSON/testes; médio com F nos gatilhos | 1.12.0 |
| F | MUNDO ABERTO ao lado do LINEAR | E integrada; design aprovado; C/D prontos para a UI | Muito alto: runtime, save, câmera, menu, performance | 2.0.0 |
| G | Assinatura visual por dimensão | D e F integradas; protótipo de 2 dimensões + nave aprovado | Alto com D/F: cenários, sprites, shaders e legibilidade | 2.1.0 |

### Ajustes sugeridos, sujeitos à aprovação

1. **A é bloqueante externo.** O resultado do Windows e a origem dos binários
   precisam ser decididos antes de qualquer tag. Enquanto isso, é possível
   revisar branches, mas não misturar release com fase seguinte.
2. **B4:** se o parallax/som depender da estrutura final do menu, fazer B4
   **depois do piloto de C** reduz retrabalho. Se for mantido em B, C terá de
   preservar esses comportamentos. Recomendo decidir isso antes de começar B4.
3. **E pode ser intercalada** por alterar quase só JSON e testes. Recomendo
   quatro PRs separados (capítulos 3, 4, 5 e 6), sempre rebaseados na main, e
   não misturar com F.
4. **F pode ter o design revisado e integrado cedo**, sem código, desde que a
   implementação continue depois de E. O documento atual está defasado e
   precisa ser rebaseado e confrontado com o que já entrou em B/C/D.
5. **G só depois de D e F.** O protótipo de duas dimensões e da nave deve ser
   aprovado antes de qualquer expansão.

## 4. Matriz de conflitos

| Par | Risco | Áreas prováveis |
| --- | --- | --- |
| A × todas | Alto | `pyproject.toml`, tags, README, CHANGELOG, artefatos e versão. |
| B × C | Alto | `menu.py`, `theme.py`, layout, componentes e testes do menu. |
| B × D | Médio | Tema, fontes, HUD e composição do menu. |
| B × F | Alto | Menu JOGAR, modo atual, foco e retomada. |
| C × D | Alto | Tokens, HUD, fontes, telas e caches de desenho. |
| C × F | Alto | Telas, navegação e componentes que o mundo aberto reutiliza. |
| D × G | Alto | Cenários, sprites, shaders, contraste e caches. |
| E × F | Médio | Gatilhos narrativos, progressão, bosses e JSON de cenas. |
| F × G | Alto | Fundos das regiões, entidades, renderização e performance. |

## 5. Numeração de versões

Adotada a ordem padrão e a release primeiro:

- **1.8.0** — fechamento da candidata atual, sem novo conteúdo de fase.
- **1.9.0** — B4 e aceitação final do menu.
- **1.10.0** — C, kit de UI e migração das telas.
- **1.11.0** — D, polimento visual residual.
- **1.12.0** — E, capítulos 3–6, minibosses e final.
- **2.0.0** — F, novo modo e possível mudança de schema de perfil.
- **2.1.0** — G, assinatura visual por dimensão.

Esses números são lugares na sequência, não versões reservadas. Se B4 for
movido para depois de C, ou se E for intercalada, a numeração deve ser refeita
no momento da integração. A versão de release só é fechada quando a ordem real
de merge e a compatibilidade de dados estiverem definidas.

## 6. Decisões pendentes antes de começar

1. **A:** qual resultado do teste Windows foi obtido e quais hashes foram
   aprovados?
2. **A:** a 1.8.0 será a RC `f383926`, o build da PR #36 ou uma nova RC da main
   atual? Não anexar binário de um commit a uma tag de outro.
3. **A:** o que fazer com a PR #36 — rebase, reconstrução ou fechamento?
4. **B:** B4 entra antes ou depois do piloto de C?
5. **C:** o piloto local de Recordes (`feat/ui-kit-c`) será rebaseado e usado
   como tela-piloto, ou o piloto será refeito?
6. **D:** D1/D2 locais serão reaproveitados após rebase? Quem aprova as
   capturas antes/depois?
7. **E:** o capítulo 3 será revisado a partir de `docs/roteiro-capitulo-3.md` e
   a branch 3–6 será dividida em quatro PRs?
8. **F:** o design de mundo aberto continua com as decisões da seção 15 do
   documento atual, após confronto com B/C/D?

## 7. Critérios comuns

- Uma branch por fase, criada de `origin/main` atualizada, em worktree limpo.
  Push por etapa e PR antes de qualquer merge. Tag de segurança na
  `origin/main` antes de cada merge aprovado.
- Não tocar na main local, no checkout original, nas branches antigas, nas tags
  ou nos worktrees existentes. Sem force push, `reset --hard` ou remoção de
  worktrees sem pedido.
- Passo 0 de cada fase: plano/design e parada para aprovação antes do código.
- TDD para lógica pura; suíte completa e Ruff nos arquivos alterados antes de
  cada push. Benchmark antes/depois com média, p95, várias rodadas e o mesmo
  ambiente. Em etapa só de documentação, registrar "não aplicável".
- Commits pequenos em Conventional Commits. Atualizar `CHANGELOG.md`, README,
  `AI_USAGE.md` e `ROADMAP.md` conforme o que foi realmente integrado.
- Acessibilidade: redução de efeitos, no máximo 3 flashes por segundo, nada
  dependente só de cor, contraste ≥ 4,5:1 para texto essencial e ≥ 3:1 para
  secundário, texto em pixels efetivos e zero cortes nas quatro resoluções, nos
  modos AJUSTAR/PREENCHE e nos estilos ORIGINAL/COMIC.
- Capturas e GIFs reais em SDL dummy, não mockups, nos pontos de parada visual.
- Sem dependências novas além do pygame. Assets procedurais ou com licença
  livre registrada.

## 8. Estado deste Passo 0

- Branch: `docs/roadmap-fases-passo0`.
- Worktree: `/tmp/incarnate-roadmap-passo0-20261024`.
- Base: `origin/main` `63ae5dc`.
- Nenhum código de jogo foi alterado.
- Testes, Ruff e benchmark: não aplicáveis a esta entrega documental.
- Nenhuma tag, PR de merge ou alteração na main foi criada.
- **Parada para aprovação do usuário antes de iniciar a Fase A.**
