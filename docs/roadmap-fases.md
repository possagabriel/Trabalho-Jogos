# Plano de fases do INCARNATE — Passo 0

Inventário feito em 24/10/2026 sobre `origin/main` em `cbe4702`. Este documento é
uma proposta para aprovação. Nenhuma fase de implementação começa com este PR.
O [ROADMAP](../ROADMAP.md) continua sendo a memória do projeto: atualizar seu
estado a cada integração, junto com `CHANGELOG.md` e `AI_USAGE.md`.

## Inventário e diferenças entre o pedido e a main

- `origin/main` está em `cbe4702` (#33). A `main` local está em `bebe716` e não
  foi atualizada. O checkout original, em `fix/build-limpa-moedas-tiros`, contém
  alterações locais e arquivos não rastreados; deve permanecer intocado.
- Há 27 branches remotas, incluindo `main`, 8 tags remotas (3 de segurança,
  `v0.0.1`, `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.8.0-rc1`) e nenhum PR aberto no
  inventário da API do GitHub. Os PRs #29 a #33 foram integrados. Existem 17
  worktrees registrados antes deste plano: o checkout original e 16 entradas
  antigas em `/tmp`, marcadas como *prunable* porque os diretórios não existem.
  Não limpar nem remover essas entradas sem pedido específico. Este plano usa
  um novo worktree em `/tmp` e branch própria.
- A tag `v1.8.0-rc1` aponta para `f383926`. O documento de distribuição relata
  builds Linux/Windows concluídos, mas o checklist manual Windows e a decisão
  de release ainda dependem do usuário. Não há tag `v1.8.0` publicada.
- A licença MIT, o texto OFL e sua inclusão no instalador/pacote Linux, as
  instruções de SmartScreen/SHA-256 e a limpeza Ruff já estão na main pelos
  PRs #29/#30. Não repetir essas mudanças na Fase A. O `ROADMAP.md` ainda as
  lista como pendências e precisa ser corrigido na próxima etapa aprovada.
- O menu de cinco destinos, os hubs Jogar/Perfil, foco, nomes truncados, cartão
  de perfil, resumos, selos e composição 4:3 estão na main pelo PR #31. As
  etapas 1 a 3 da Fase B passam a ser auditoria de aceitação, com correções
  pontuais se a revisão visual as encontrar. Sons já usam `_som()` no menu;
  falta verificar a cobertura de eventos. `ParallaxBackground` existe no mundo,
  mas não há evidência de uso no menu principal. A etapa 4 segue candidata.
- O JSON de produção `src/runtime/story/cenas_pt_BR.json` contém introdução e
  capítulo 1; não contém capítulo 2. O usuário forneceu o texto completo de
  [CAPÍTULO 2 // FUNÇÃO](roteiro-capitulo-2.md) após o inventário. É fonte de
  roteiro para E, ainda sem integração no motor. Conferir se há uma versão
  aprovada fora da main antes de adaptar o texto ao JSON.
- O ROADMAP indica que HUD/tipografia, fundos por dimensão e contornos já foram
  integrados nas versões 1.6 a 1.8. D deve auditar e concluir ícones, estados e
  sequências pendentes; não refazer as etapas que já passaram.
- O ponto de `Continuar` exibido hoje é Dimensão 1/Nível 1 porque esse é o
  ponto iniciado pelo callback atual; o Lobby retoma checkpoint. O pedido de
  "ponto realmente carregado" deve ser avaliado contra esse fluxo, sem
  prometer retomada integral do estado da partida.

## Ordem proposta e dependências

| Ordem | Unidade de integração | Dependências e parada | Risco principal / conflito |
| --- | --- | --- | --- |
| A | Fechamento da RC e pendências verificadas | Resultado Windows e decisão sobre apóstrofo; aprovação do plano antes de código ou release | Alto com release: main avançou desde a RC; evitar tag sobre binário de outro commit |
| B | Aceitação do menu já integrado; etapa 4 e correções comprovadas | A integrada; captura real antes/depois da etapa 3 já integrada e nova parada visual | Médio com C: `src/runtime/presentation/menu.py`, tema e layout |
| C | Inventário de telas, kit e migração uma tela por vez | B integrada; aprovar tela-piloto antes das demais | Alto com B/D/F: menu, telas e navegação |
| D | Resto do polimento visual, após auditoria de paridade | C integrada; aprovar cada etapa, inclusive a decisão sobre texto/HUD na resolução final | Médio/alto com C/G: HUD, fontes, cenários, caches e compositor |
| E | Integrar capítulo 2 fornecido; roteiro 3 a 6, minibosses e final | Conferir versão aprovada do capítulo 2 e aprovar cada capítulo; capítulo 6 antes das revelações de F | Baixo com B/C/D; médio com F se mudar o catálogo/gatilhos |
| F | MUNDO ABERTO mantendo LINEAR idêntico | E integrada por padrão; documento de design e decisões de mapa/save antes de código; protótipo e GIFs após câmera/fundo | Muito alto: runtime, persistência, câmera, eventos, performance |
| G | Assinatura gráfica por dimensão | F integrada e regiões disponíveis; aprovar protótipo de duas dimensões + nave | Alto com D/F: cenários, sprites, renderização CPU/GPU e legibilidade |

Manter A → B → C → D → E → F → G como ordem padrão de integração, pois C
define a interface que F exibirá, e E define a progressão narrativa de F. A
única antecipação sugerida é **conferir a origem do capítulo 2**, já registrado
como texto de referência, para não construir F sobre uma premissa incorreta. Se
houver autorização para intercalar E, fazê-lo em PRs/branches separados por capítulo,
sempre sobre a `origin/main` que já contiver a fase anterior aprovada. Não
misturar mudanças de UI, motor e roteiro na mesma branch. O conflito estimado
é por arquivos e contratos conhecidos; será reavaliado ao abrir cada fase.

## Versões pela ordem efetiva de integração

`pyproject.toml` já está em `1.8.0`, mas os PRs #29 a #33 entraram na main
*depois* de `v1.8.0-rc1`. Há duas saídas, sujeitas à decisão de release:

1. **Proposta:** após checklist Windows aprovado, promover exatamente os
   binários de `v1.8.0-rc1` e marcar `v1.8.0` no mesmo commit `f383926`.
   Mudanças posteriores da main entram na próxima versão. Verificar os hashes,
   o commit de build e os artefatos antes de publicar. Não reconstruir e chamar
   o resultado de "binários testados".
2. Se `v1.8.0` tiver de representar a `origin/main` atual, gerar nova RC dessa
   revisão, testar os novos binários no Windows e só então lançar. A RC antiga
   não cobre os PRs #29 a #33.

Adotada a opção 1 e a ordem padrão acima, o *marco de conteúdo* seguinte será
`1.9.0`: mudanças de menu já integradas mais o complemento de B, quando aprovado.
Projeção condicional de marcos seguintes: C `1.10.0`, D `1.11.0`, E `1.12.0`,
F `2.0.0` (novo modo e schema; avaliar compatibilidade no design) e G `2.1.0`.
A não ganha número próprio se só fechar a release antiga; correções de A que
chegarem à main após a RC entram no próximo marco. Esses números são lugares na
sequência, não versões reservadas: reordenar, dividir ou intercalar PRs muda a
numeração. Definir a versão somente quando a ordem real de merge e o alcance
de compatibilidade estiverem fechados. Cada release candidata solicitada pelo
usuário usa tag `rc` própria sobre commit exato e checklist Windows.

## Escopo e pontos de decisão por fase

### A — fechamento

Receber o resultado do teste Windows da RC: instalação limpa, atualização,
atalhos, jogo, perfis, desinstalação e conferência dos hashes. Separar release
dos itens já integrados. Decidir com o usuário se novos nomes de perfil aceitam
apóstrofo; a regra atual rejeita, enquanto perfis antigos permanecem legíveis.
Qualquer mudança terá migração/testes que preservem nomes existentes. Confirmar
se o PR #33 exige uma nova RC ou se pertence somente à versão seguinte.

### B — menu ORIGINAL e COMIC

Auditar as oito combinações de resolução e AJUSTAR/PREENCHER em ambos os estilos,
com e sem save. Conferir defeitos listados nas etapas 1–3, navegação em até duas
ações, Esc/foco, Continuar, cartão, selos e dados. Mostrar capturas reais
antes/depois e parar antes de correções de design. Na etapa 4, mapear sons por
ação, testar fundo de menu com `ParallaxBackground` e cache estático em BAIXA,
e verificar animações, flashes e desempenho. Preservar a jogabilidade LINEAR.

### C — kit de UI e telas

Registrar matriz de inconsistências para lobby, hangar/loja, recordes,
configurações, perfis, Arquivo de Memórias, Continuar, pausa, game over,
melhorias, confirmações, notificações e diálogos de cutscene. Definir tokens
por ORIGINAL/COMIC e contratos de Panel, Button, TabBar, ListView, Toggle,
Slider, TextInput, ConfirmDialog, Toast, ScreenHeader, FooterHints,
EmptyState e Scrollbar. Documentar navegação, sons, transições e vocabulário.
Fazer uma tela-piloto e parar para aprovação; depois migrar uma tela por commit,
com capturas antes/depois. Dividir `menu.py` por responsabilidade, mantendo
callbacks e estado idênticos.

### D — polimento visual residual

Verificar o que já entrou nas etapas 2–5. Decidir com medição se HUD e texto
devem ser rasterizados na resolução final: comparar nitidez, custo de escala,
cache, CPU/GPU e risco em PREENCHE. Conferir saliência dos fundos, ícones e
estados, contornos e sequências de explosão, troca de dimensão, boss e transição.
Cada etapa tem comparação real e aprovação; hitboxes e balanceamento ficam
intocados sem autorização específica.

### E — roteiro

Resolver primeiro a ausência do capítulo 2 no JSON, usando o
[texto recebido](roteiro-capitulo-2.md) após conferir sua versão aprovada.
Revisar um capítulo por vez: 3
(Identidade/ESTRELA/fragmentos do Jonathan humano), 4 (Silêncio/PENTAGONO/
mensagem interrompida), 5 (Descarte/ANEIS/cópias) e 6 (origem do Protocolo
Cristal/ANEIS DOURADO/final narrativo sem encerrar a partida). Acrescentar falas
de minibosses com léxico próprio. Nomes de Protocolos Restritos aparecem apenas
em título ou glitch, jamais em fala; manter frases curtas e ordem de revelações.
Alterar somente JSON e testes do roteiro, salvo decisão nova aprovada.

### F — LINEAR e MUNDO ABERTO

O design deve comparar mapa em dados com geração procedural por semente,
especificar sistemas compartilhados e saves por modo, com migração versionada.
Proposta inicial para decisão: skins, Memórias e estatísticas compartilhadas;
moedas, armas, melhorias e posição por modo. JOGAR escolhe modo; CONTINUAR
retoma o último. O LINEAR precisa de testes de paridade. Protótipo: uma região,
uma toca de boss, 3–5 destroços, estação e perigo, câmera e fundo ligados à
posição. Parar com GIFs reais após câmera/fundo. Só depois expandir regiões,
fendas, patrulhas, radar, mapa com névoa, viagem rápida, Espaço Nulo e bloqueios
narrativos. Entidades por chunks e orçamento de frame medido.

### G — assinatura visual das dimensões

Protótipo renderizado com duas dimensões e a nave; aprovar antes das demais.
Explorar vetor limpo, halftone de duas tintas, aquarela, facetado/vitral,
pixel 1-bit com dithering e dourado ornamental; núcleo luminoso e rachaduras
progressivas na nave. Manter HUD, mira, menu, fonte e contorno da nave como
identidade comum. Strategy por dados, cache por estilo, transição sem pop e
fallback CPU para shader opcional. Medir contraste e saliência de inimigos e
projéteis; aplicar às regiões de F sem mudar hitboxes.

## Critérios comuns para as próximas fases

- Passo 0 de cada fase: plano/design e parada para aprovação **antes do código**.
  Branch exclusiva em worktree limpo baseada na `origin/main` atualizada; push
  por etapa, PR antes de qualquer merge, tag de segurança na `origin/main` antes
  do merge aprovado. Preservar branches, tags, worktrees, main local e alterações
  locais. Sem force push, `reset --hard` ou dependências novas além de pygame.
- TDD para lógica pura. Rodar testes da área antes/depois, suíte completa e
  Ruff nos arquivos Python alterados antes de cada push. Benchmark antes/depois
  no mesmo ambiente, com múltiplas rodadas, média e p95; registrar cenário,
  versões e dispersão. Em etapa só de documentação, registrar "não aplicável"
  para benchmark e Ruff de Python, sem inventar métricas.
- Acessibilidade em cada tela: redução de efeitos respeitada, no máximo três
  flashes por segundo, nenhum estado comunicado só por cor, contraste de texto
  essencial ≥ 4,5:1 e secundário ≥ 3:1, métricas de fontes em pixels efetivos
  e zero cortes nas quatro resoluções, dois modos de escala e dois estilos.
- Em cada ponto visual, fornecer capturas/GIFs do Pygame real em SDL dummy,
  não mockups conceituais. Comparar antes/depois quando houver mudança. Medir
  legibilidade de inimigos/projéteis sobre o fundo, sem alterar colisão.
- Commits pequenos em Conventional Commits; atualizar `CHANGELOG.md`, README,
  `AI_USAGE.md` e `ROADMAP.md` conforme o que foi realmente implementado.
  Entregar design, testes, benchmark, imagens, PR com riscos e checklist Windows.
  Assets novos precisam ser procedurais ou ter licença livre registrada.

Backlog opcional: game feel, dificuldade/ranking, gamepad, acessibilidade
adicional, voz/música, tutorial, conquistas, log, CI de benchmark, type hints,
replays, tradução, itch.io e checagem de versão. Nenhum item entra em A–G sem
pedido explícito.
