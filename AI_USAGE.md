# Registro de uso de IA

## Menu principal — etapa 3: cartão e layout responsivo

- **Pedido:** adicionar cartão de perfil, resumo de Continuar, selos de novidade,
  composição 4:3 e retirar telemetria decorativa sem dados; manter ORIGINAL e
  COMIC com a mesma estrutura antes de apresentar capturas reais.
- **Implementação da IA:** o cartão e os resumos consultam `ProfileService`; o
  schema v3 guarda novidades pendentes do Hangar para não reaparecerem após
  oscilação de moedas; perfis antigos recebem defaults e exportação/importação
  preserva os campos. O HUD conserva molduras/cantos neon e remove rótulos falsos.
- **Decisões:** Continuar mostra Dimensão 1 / Nível 1, que é o ponto iniciado
  pelo callback atual, e o tempo total do perfil; Lobby continua retomando o
  checkpoint. Layout 4:3 ajusta a apresentação sem ampliar a área jogável.
- **Verificação:** testes direcionados de perfis/menu: 122 passaram. Suíte
  completa: 639 passaram, 1 ignorado. Ruff limpo nos nove arquivos Python
  alterados.
- **Capturas reais:** antes/depois em ORIGINAL e COMIC, quatro resoluções,
  AJUSTAR e PREENCHE, menu principal e hub Jogar, com e sem save estão em
  `/tmp/incarnate-menu-stage3-audit/`.
- **Benchmark:** SDL dummy, ORIGINAL, 1920×1080, 40 quadros de aquecimento,
  12 rodadas de 100 quadros. Antes: média 7,750 ms, p95 12,664 ms, desvio das
  médias por rodada 1,129 ms. Depois: média 8,539 ms, p95 12,234 ms, desvio
  0,474 ms. A média aumentou 10,2% e o p95 caiu 3,4%; a dispersão entre
  rodadas ficou menor que a da referência. O benchmark mede o desenho do menu,
  não o passo de apresentação da janela.
- **Ajustes manuais do usuário:** nenhum informado.

## Menu principal — estrutura e dados (1.8.0)

- **Pedido:** reorganizar ORIGINAL e COMIC em Jogar, Hangar, Perfil,
  Configurações e Sair; preservar callbacks, permitir retorno com foco de
  origem, guardar avisos reconhecidos e documentar a navegação.
- **Implementação da IA:** dois hubs de segundo nível; migração do schema de
  perfil para registrar novidades de Memórias e Hangar; consulta e confirmação
  de novidades pelo `ProfileService`; testes de transferência e de aviso único.
- **Decisões:** Continuar abre a tela existente de progresso/Novo Jogo para
  preservar esse fluxo e inicia na Dimensão 1 / Nível 1. O checkpoint fica no
  Lobby. O tempo exibido é total do perfil.
- **Ajustes manuais do usuário:** nenhum informado.
- **Verificação:** suíte completa: 632 passaram, 1 skip. Ruff nos arquivos
  alterados: limpo. Testes adicionados para hubs, foco/retorno, migração de
  perfil, exportação/importação e reconhecimento dos avisos.

## Menu ORIGINAL — etapa 2: hierarquia e animação

- **Pedido:** organizar Continuar, Lobby e Hangar como ações principais e agrupar
  os itens secundários, preservando numeração, navegação e callbacks; mostrar a
  comparação em quatro resoluções e nos modos AJUSTAR e PREENCHE.
- **Implementação da IA:** tamanhos e posições por grupo foram centralizados nos
  tokens de `theme.py`; indicador de foco, faixa selecionada, textos estáticos e
  título usam cache. A nave ocupa o espaço livre à esquerda. O título recebe
  glitch cromático breve limitado a 42 ms a cada 650 ms (menos de 3 pulsos/s),
  respeitando `intensidade_flash` NORMAL, REDUZIDO e DESLIGADO. O estilo COMIC
  mantém seu layout e seu HUD anteriores.
- **Decisões:** a seleção segue contínua entre os grupos e continua começando em
  Continuar com save ou Lobby sem save. Continuar sem save mantém o visual
  desabilitado e o aviso existente ao ativar. A validação do `ProfileService`
  rejeita apóstrofo em novos nomes; perfis antigos não são alterados. A tela
  trata nomes longos com reticências e caracteres acentuados.
- **Comparação visual:** imagens ANTES/DEPOIS das quatro resoluções e dos dois
  modos, além do mockup 1920×1080, estão em
  `/tmp/incarnate-menu-audit-2026-10-18/etapa2`; esses arquivos não são incluídos
  no repositório. Duas capturas JPEG otimizadas foram adicionadas ao README.
- **Benchmark do menu:** SDL dummy, estilo ORIGINAL, resolução lógica 1280×720,
  30 quadros de aquecimento e 8 rodadas de 100 quadros. Na main anterior: média
  7,589 ms, p95 10,335 ms e desvio das médias por rodada 0,315 ms. Após a etapa
  2: média 7,608 ms, p95 9,632 ms e desvio 0,360 ms; a média variou 0,25%, dentro
  da variação entre rodadas.
- **Verificação:** suíte completa: 622 passaram e 1 foi ignorado. Os testes
  direcionados do menu/perfis/layout somaram 127 aprovações. Ruff passou nos seis
  arquivos Python alterados.
- **Ajustes manuais do usuário:** nenhum informado.

## Menu ORIGINAL — etapa 1: correções visuais

- **Pedido:** corrigir cortes, sobreposições, contraste e margens do menu neon;
  manter ações e ordem de navegação; diferenciar Continuar sem save.
- **Implementação da IA:** rótulos são ajustados dentro dos botões, cuja área
  clicável acompanha o desenho e a animação de entrada; linhas decorativas ficam
  no espaço negativo; subtítulo e rodapé ganharam fundo/cores de alto contraste;
  texto de perfil recebe reticências quando excede a largura calculada. A seleção
  inicial escolhe Continuar com save e Lobby sem save.
- **Apóstrofo:** `ProfileService` rejeita `'` em criação e renomeação. A regra foi
  mantida; teste confirma que a tentativa de renomear falha sem mudar o perfil
  existente. A renderização do menu continua aceitando nomes legados já salvos.
- **Decisões:** callbacks do menu e gameplay permaneceram intactos. A versão do
  rodapé lê `project.version`; a fonte única já havia sido introduzida no commit
  `83be260`. Glitch e animações novas ficam para as etapas posteriores aprovadas.
- **Ajustes manuais do usuário:** nenhum informado.
- **Auditoria:** capturas originais e etapa 1 em
  `/tmp/incarnate-menu-audit-2026-10-18`; arquivos fora do repositório.
- **Verificação:** 617 testes passaram e 1 foi ignorado. Ruff passou nos sete
  arquivos Python alterados. Testes cobrem nome com apóstrofo, limites de texto,
  cliques nas oito combinações de resolução/modo, seleção inicial e contraste
  amostrado sobre o fundo real incluindo o planeta.

## Fallback de inicialização gráfica

- **Pedido:** investigar o segmentation fault de `python main.py` na criação da
  janela de vídeo, sem alterar a `main` local.
- **Implementação da IA:** ao falhar a criação do apresentador OpenGL, registra
  o erro, encerra e reinicia o subsistema de vídeo antes de tentar a janela CPU.
- **Verificação:** teste unitário confirma a ordem OpenGL → quit → init → CPU;
  após atualizar com `origin/main`, 603 testes passaram e 1 teste OpenGL foi
  ignorado. Ruff passou nos dois arquivos Python alterados e
  `main.py --smoke-test` passou.
- **Ajustes manuais do usuário:** nenhum informado.

## Fase 1 — Mira customizada (1.2.0)

- **Pedido:** criar a mira cartoon por dimensão, orientar disparos para o mouse,
  preservar o teclado, adicionar pulso e feedback sobre inimigos, opção salva
  em JSON e overlay F3; trabalhar em `feature/mira` a partir de `main` limpa.
- **Implementação da IA:** cálculo puro de direção e dispersão, integração do
  botão esquerdo e das teclas no gameplay, sprites de mira em cache, cursor SDL
  normal fora do combate, configuração persistente retrocompatível, overlay de
  debug, testes TDD, README e changelog.
- **Ajustes manuais do usuário:** nenhum informado nesta fase. As alterações
  locais do diretório de trabalho original não foram modificadas.
- **Decisões:** armas direcionais seguem a mira; Duplo e Espiral distribuem os
  tiros ao redor da direção central, com `dispersao_duplo_graus` e
  `dispersao_espiral_graus` no `settings.json` do diretório de dados do usuário.
  **Limitação conhecida:**
  Íon permanece em coluna vertical e não acompanha a mira. Teclado dispara
  verticalmente se a mira estiver desligada ou fora da área do jogo. F3 mostra
  zero camadas de parallax nesta fase; o fundo dinâmico pertence à fase 2.
- **Verificação:** baseline da `main` limpa: 434 testes passaram, 0 falharam.
  Depois da implementação: 446 testes passaram, 0 falharam. Medição isolada
  da mira com 50 hitboxes em SDL dummy: 0,0043 ms por quadro em 1.200 quadros.

## Atualização da fase 1 — sprites direcionais

- **Pedido:** fazer a nave mudar conforme a mira e criar as sprites necessárias.
- **Implementação da IA:** orientação calculada pelo alvo do tiro, 48 quadros
  gerados e cacheados por skin e perfil visual, com poses para transparência,
  cristal, asas e relâmpagos; partículas de chamas seguem a traseira da nave.
- **Ajustes manuais do usuário:** nenhum informado nesta atualização.
- **Decisões:** todas as dez skins acompanham a mira; a hitbox não gira. Com a
  mira desligada ou fora da área de jogo, mantém-se o desenho anterior.
- **Verificação:** 462 testes passaram, 0 falharam. Prévia das dez skins nos
  perfis ORIGINAL e COMIC; primeira geração da skin padrão em SDL dummy:
  6,56 ms, quadros cacheados: 0,006 ms por desenho (1.200 repetições).

## Fase 2 — Avanço da nave (1.3.0)

- **Pedido:** sensação contínua de avanço por rolagem 2D, parallax, linhas de
  velocidade, frenagem em bosses, retomada na derrota, salto dimensional,
  opções persistentes, F3, TDD e medição com mais de 50 entidades.
- **Implementação da IA:** modelo puro de quatro estados, fundos espelhados sem
  emenda, 3 a 5 camadas pré-renderizadas, pool limitado de linhas, integração
  com boss/miniboss e a transição de 64 quadros, configurações retrocompatíveis,
  brilho do propulsor, testes, benchmark e documentação.
- **Ajustes manuais do usuário:** nenhum informado.

- **Decisões:** direção fixa `[0, 1]` independente da mira; miniboss a 50% por
  padrão, com percentuais de 0% a 100% e exceções por tipo; desvio residual
  de 4% nas camadas distantes durante `PARADO`; eventos genéricos
  `BOSS_SPAWNED` e `BOSS_DEFEATED` publicados após os pontos já existentes
  de entrada e derrota, para reutilização na Fase 3.
- **Verificação:** baseline de 157 testes relacionados passou; a suíte completa
  passou com 481 testes após a integração. Benchmark do desenho e atualização visual do mundo
  com 60 inimigos e a nave em 1280×720, COMIC/MEDIA, Linux x86_64,
  Python 3.14.8, pygame-ce 2.5.8, SDL dummy: mediana de três médias de
  2,063 ms antes e 3,751 ms com avanço; p95 de 2,881 ms e 5,009 ms.
  A medição não inclui apresentação da janela nem garante 60 FPS.

## Fase 3 — História e cutscenes (1.4.0, capítulo 1 para revisão)

- **Pedido:** motor de cenas e diálogos em JSON, integração com eventos de
  boss e avanço, persistência, Arquivo de Memórias, F3 e roteiro pt-BR entregue
  um capítulo por vez.
- **Implementação da IA:** catálogo validado, sequenciador testado, entrada de
  diálogo, efeitos, controles, gate de retomada após boss, save retrocompatível,
  menu de replay, depuração e introdução/capítulo 1 em arquivo de roteiro.
- **Decisões:** nomes dos Protocolos Restritos aparecem só em títulos ou texto
  de glitch, nunca em falas. O capítulo 6 será a origem do Protocolo Cristal;
  seu final narrativo não encerrará a partida. Sem finais alternativos nesta fase.
  Os demais capítulos e falas de miniboss aguardam a revisão do capítulo 1.
- **Ajustes manuais:** nenhum informado.
- **Verificação:** 500 testes passaram na suíte completa; pulo, pausa,
  ausência de cena pós-boss, JSON inválido e fechamento no meio de uma cena
  foram cobertos. O wheel 1.4.0 inclui o JSON do roteiro.

## Fase 4 — Perfis de jogador (1.5.0)

- **Pedido:** múltiplos perfis locais com CRUD, progresso individual, migração do save único,
  recuperação de arquivos danificados e interface de seleção antes do menu.
- **Implementação da IA:** modelo versionado, repositório JSON por UUID, serviço de regras,
  seleção por teclado e mouse, integração do progresso e dos recordes ao perfil ativo,
  importação e exportação portáteis para perfis,
  testes de lógica e integração, README e changelog.
- **Decisões:** JSON por perfil; `index.json` derivado, com reconstrução por varredura;
  controles, sensibilidade e mira por perfil; som, vídeo e diálogo globais. O jogo guarda
  checkpoint de campanha, mas reinicia a partida no nível 1, então as melhorias são
  registradas apenas como contagens agregadas. Arquivos legados permanecem intactos após
  a migração. Os capítulos 3 a 6 do roteiro não foram incluídos.
- **Ajustes manuais do usuário:** nenhum informado.

## Ajuste da Fase 2 — Fundo que evolui (1.6.0)

- **Pedido:** dar sensação de percurso 2D com marcos por dimensão, evolução
  progressiva do cenário, ritmo variável, chegada de boss, configuração, F3 e
  comparação de benchmark.
- **Implementação da IA:** catálogo de marcos procedurais cartoon, cache e pool
  limitados por qualidade, sorteio reproduzível, progresso monotônico suavizado,
  curvas de evolução por dimensão, destino acionado por eventos de boss, fades
  durante troca dimensional, testes, benchmark e documentação.
- **Decisões:** a semente é aleatória por partida quando `avanco_semente` é
  `null`; números fixos permitem reproduzir testes. Minibosses não criam
  destino. O indicador de nível usa fila e inimigos ativos, sem alterar combate.
  Os marcos ficam sob as entidades jogáveis e congelam durante telas pausadas.
- **Verificação:** baseline de avanço com 60 inimigos: média 4,819 ms, p95
  6,372 ms. Após a alteração: média 5,421 ms, p95 8,850 ms, com o mesmo
  ambiente e parâmetros. Memória de cache da dimensão 1: 435.000 bytes em
  BAIXA, 610.092 em MEDIA e 753.200 em ALTA.
- **Ajustes manuais do usuário:** nenhum informado.

## Polimento do repositório (sem gameplay)

- **Pedido:** conferir as Fases 1 a 3 e atualizar README, imports, configuração de lint,
  workflows, preview do HUD, caminhos de dados, `.gitignore`, migração de arquitetura,
  versões e documentação de uso.
- **Implementação da IA:** README separado para jogadores e desenvolvedores; comandos e
  controles revisados; `tools/preview_hud.py` usa imports canônicos; Ruff centralizado no
  `pyproject.toml`; CI dispara em pushes e pull requests; adapters legados usam
  `INCARNATE_DATA_DIR` com fallback para `SPACEFURY_DATA_DIR`; `.gitignore` protege dados,
  perfis, saves e builds; mapa de migração e tabela de testes atualizados.
- **Decisões:** mantém-se o nome de comando `void-shift` por compatibilidade e adiciona-se
  `incarnate`; versão do código permanece 1.5.0 e nenhuma tag de release é criada. Foi
  proposta licença MIT para o jogo; nenhuma `LICENSE` foi aplicada. Orbitron e Rajdhani
  foram verificados como SIL OFL 1.1. Os arquivos `.flake8` e `.pylintrc` foram removidos
  após listar seus conteúdos e regras antes da remoção.
- **Ajustes manuais do usuário:** nenhum informado.

Este registro descreve a branch original em 1.5.0; a integração abaixo
preserva 1.8.0 e adia a renomeação do pacote/comando para a branch própria.

## Fase 5 — Polimento visual, etapa 1: PREENCHE

- **Pedido:** preservar a área jogável 16:9 em todas as telas e usar as faixas
  externas apenas para fundo decorativo, mantendo mira alinhada e círculos sem distorção.
- **Implementação da IA:** unificação da transformação de apresentação e mouse,
  fundo decorativo em cache para CPU/OpenGL, descrição em Config e README,
  teste de escala/mira em dois modos e quatro resoluções, e screenshot ultrawide.
- **Ajustes manuais do usuário:** nenhum informado.
- **Decisões:** `AJUSTAR` mantém letterbox; `PREENCHE` cobre as bordas com o fundo,
  sem mudar a área de combate. Nem o cenário nem o HUD são ampliados lateralmente.
- **Verificação:** 557 testes passaram e 1 foi ignorado. No benchmark de rolagem
  (120 quadros × 3 repetições, Linux x86_64, Python 3.14.8, pygame 2.5.8,
  SDL dummy, COMIC/MEDIA), média/p95 foram 1,733/2,014 ms no mundo sem avanço
  e 3,284/3,461 ms com avanço; a baseline era 1,884/2,211 ms e 3,831/4,836 ms.
  O benchmark mede mundo e entidades, não a apresentação; as médias variaram
  para baixo e não indicam custo do novo preenchimento decorativo.
  Complemento: foram adicionados testes para clique nas bordas, flash/fade em
  tela inteira, shake, Ajustar Tela em PREENCHE, redimensionamento/tela cheia e
  a geometria em 900x700. A suíte passou com 564 testes e 1 skip. Os cinco
  arquivos Python alterados passam em todas as regras configuradas do Ruff
  (E, F, I, W), sem regras ignoradas nesses arquivos. A verificação global
  encontrou 213 problemas preexistentes: 113 F401, 50 I001, 31 E741, 8 E501,
  6 F841 e 5 W292. Recomendo limpá-los em `chore/ruff-baseline`, sem adicionar
  exceções globais ao `pyproject.toml`.
- **Apresentação:** em SDL dummy, 7 rodadas de 120 quadros, PREENCHE/COMIC/MEDIA;
  2560x1080: média 8,221 ms, p95 9,500 ms, desvio das médias de rodada 0,160 ms
  (faixa 8,009–8,448); 1920x1080: 7,475/8,694 ms, desvio 0,125 ms
  (7,335–7,714); 900x700: 3,432/4,147 ms, desvio 0,087 ms (3,366–3,606).
  A superfície de borda manteve a mesma identidade durante as rodadas; seus
  pixels ocupam 10,55 MiB, 7,91 MiB e 2,40 MiB, respectivamente. O conteúdo é
  repopulado quando muda a cena/estilo ou o tamanho, sem alocação por quadro.
  O benchmark do mundo não foi afetado por esta etapa; a variação entre as
  rodadas antes/depois foi 0,090/0,020 ms sem avanço e 0,059/0,088 ms com avanço
  (desvio das médias, respectivamente), portanto a diferença observada é ruído.

## Fase 5 — Polimento visual, etapa 2: HUD e tipografia

- **Pedido:** legibilidade do HUD em pixels efetivos, contraste essencial de ao menos
  4,5:1, brilho restrito a foco/boss/transições e comparação de performance.
- **Implementação da IA:** HUD em surface nativa do viewport 16:9, fontes com altura de
  tinta mínima (18 px essencial, 14 px secundária), ajuste de contraste, tokens de tema,
  painel escuro nos medidores e plaquetas do boss, redução de brilho e cache da surface
  até redimensionar.
  O medidor circular agora desenha diretamente no canvas, sem surface temporária por quadro.
- **Decisões:** manter mundo e hitboxes na resolução lógica; renderizar somente o HUD na
  resolução efetiva da janela. Em 900×700 o HUD ocupa o viewport 900×506, centrado na
  janela. A qualidade de texto melhora; o custo medido do desenho do HUD aumenta porque
  seu canvas passa a ter resolução de saída. O passo de escala quase não muda.
- **Ajustes manuais do usuário:** nenhum informado.
- **Verificação:** contraste e alturas de glifos cobertos por testes; benchmark SDL dummy,
  COMIC/MEDIA, janela 1920×1080, 30 inimigos, 80 projéteis e 180 partículas. Sete rodadas
  de 120 amostras (840 no total), média/p95 em ms; o último valor por grupo é o desvio
  padrão das médias entre rodadas:

  | Medida | Antes | Depois | Desvio antes/depois |
  | --- | ---: | ---: | ---: |
  | Desenho do HUD | 1,451 / 1,797 | 2,655 / 3,063 | 0,034 / 0,032 |
  | Apresentação | 4,996 / 6,151 | 5,047 / 6,342 | 0,130 / 0,311 |
  | Quadro completo | 12,347 / 13,602 | 13,700 / 15,364 | 0,137 / 0,365 |

  O acréscimo do quadro completo foi 1,353 ms na média; a apresentação variou 0,051 ms.
  A superfície do HUD é reutilizada entre quadros e recriada apenas quando muda o tamanho
  do viewport. Capturas comparativas completas ficam fora do repo;
  a imagem-chave do README está em `docs/screenshots/hud-900x700.jpg`.
  A suíte completa passou com 571 testes e 1 skip; os arquivos Python alterados passaram
  em todas as regras Ruff ativas. A verificação global ainda aponta 204 achados anteriores
  fora desta etapa. Foram gerados GIFs locais de explosão, troca de dimensão, entrada de
  boss, frenagem/aceleração e transição do menu em `/tmp/incarnate-visual-audit-20261018/etapa2/animacoes`;
  os efeitos mantêm continuidade, a entrada do boss é legível e o menu de primeira execução
  mostra corretamente a seleção/criação de perfil.

## Fase 5 — Polimento visual, etapa 3: cutscenes

- **Pedido:** aplicar acabamento cartoon barato aos fundos rasterizados já existentes,
  sem trocar assets, e alinhar caixa, retratos e títulos à guia aprovada; magenta somente
  para glitch/alerta.
- **Implementação da IA:** cache de posterização em paleta curta, tinta por dimensão,
  contorno e retícula; passagem opcional no fundo da partida e do menu durante cutscenes;
  contornos de texto, retratos com moldura de tinta e painéis sem glow decorativo. As
  superfícies de atores e as regras de gameplay permanecem fora do filtro.
- **Ajustes manuais do usuário:** nenhum informado.
- **Verificação visual e performance:** capturas antes/depois e GIF curto em
  `/tmp/incarnate-visual-audit-20261018/etapa3`; imagem-chave em
  `docs/screenshots/cutscene-dialogue.jpg`. Benchmark headless de cutscene, cena fixa em
  1280×720, cinco rodadas de 30 quadros: baseline 19,710 ms de média e 25,831 ms de p95
  médio (desvio entre médias 1,537 ms); após 19,514/24,516 ms (desvio 1,367 ms). A
  diferença fica dentro da variação entre rodadas. O filtro custou 29,001 ms na primeira
  geração, caindo a 0,0027 ms no acesso seguinte (3,52 MiB por surface de saída). Na
  sequência animada, o capítulo mantém o quadro de título, o texto se revela sem salto,
  e a fala de glitch alterna variantes curtas sem tremer a moldura ou borrar retratos.

## Fase 5 — Polimento visual, etapa 4: fundos por dimensão

- **Pedido:** diferenciar a composição dos seis fundos COMIC, preservar a leitura
  dos projéteis e respeitar os marcos integrados na main, sem alterar gameplay.
- **Implementação da IA:** composições procedurais com rotas orbitais, cristas
  vulcânicas, ondas/recifes, cristais, fenda e raios/anéis; redução da densidade
  de destroços; contorno escuro e claro nos projéteis inimigos. Hitboxes não mudam.
- **Decisões:** superfícies do fundo continuam pré-renderizadas e cacheadas por
  dimensão/qualidade. O par de contornos oferece ao menos 3:1 de contraste com
  fundos claros ou escuros; o limite está centralizado nos tokens de estilo.
- **Ajustes manuais do usuário:** nenhum informado.
- **Verificação visual:** referências das seis dimensões, comparativo e GIF real
  da troca de dimensão ficam em `/tmp/incarnate-visual-audit-20261018/etapa4`;
  `docs/screenshots/dimensoes-composicao.jpg` é a imagem otimizada incluída no README.
- **Benchmark:** preview COMIC/MEDIA, 30 inimigos, 80 projéteis e 180 partículas,
  SDL dummy, 1280×720, 120 amostras. Quadro completo: antes 12,330/13,094 ms
  (mediana/p95); depois 12,179/13,014 ms. Mundo: 1,698/1,814 → 1,645/2,003 ms.
  Diferenças pequenas, sem regressão observada no quadro completo; fundos e
  composições são preparados fora do caminho por quadro. A suíte completa passou
  com 599 testes e 1 skip; Ruff passou nos arquivos Python alterados.

## Fase 5 — Polimento visual, etapa 5: sprites

- **Pedido:** uniformizar contornos e dimensionar as hachuras por sprite, sem
  encobrir hitboxes ou alterar gameplay.
- **Implementação da IA:** contorno adaptativo com limite compartilhado para
  polígonos, círculos e imagens; espaçamento de hachura diminui com o tamanho,
  e sprites abaixo de 18 px não recebem hachura. A geometria de colisão não foi tocada.
- **Decisões:** arte menor mantém menos ruído; objetos grandes recebem mais detalhe.
  Superfícies ainda passam pelo cache existente; contornos externos não entram nas
  retângulos de colisão.
- **Ajustes manuais do usuário:** nenhum informado.
- **Verificação visual:** contatos antes/depois e GIFs de explosão, troca dimensional,
  boss, avanço/frenagem e menu em `/tmp/incarnate-visual-audit-20261018/etapa5`;
  screenshot compacta em `docs/screenshots/sprites-comic.jpg`.
- **Benchmark:** SDL dummy, 1280×720, COMIC/MEDIA, 30 inimigos, 80 projéteis,
  180 partículas, sete rodadas de 120 quadros. Quadro completo antes/depois:
  média 12,963/12,394 ms; p95 14,357/13,129 ms; desvio das médias por rodada
  0,141/0,065 ms. Média dos p95 de cada rodada: 14,464/13,145 ms. No mundo
  isolado: 5,419/5,273 ms de média e 5,880/5,565 ms de p95. O quadro completo
  permaneceu dentro da variação entre rodadas. A suíte completa passou com 600
  testes e 1 skip; Ruff passou nos arquivos Python alterados.

## Integração do polimento do repositório (1.8.0)

- **Pedido:** integrar a documentação, o Ruff, o CI e a unificação de caminhos de
  dados da branch `chore/polir-repo`, sem mudanças de gameplay.
- **Implementação da IA:** README em duas partes, preview HUD em `tools/`,
  caminhos de dados compatíveis com o legado, revisão do `.gitignore` e do mapa
  de arquitetura, além de CI que verifica os arquivos Python alterados.
- **Decisões:** a versão permanece 1.8.0; nome do pacote, comando e instalador
  serão tratados na branch de renomeação separada. Os registros anteriores de
  uso de IA foram preservados. `.flake8` e `.pylintrc` foram removidos após
  consolidar as regras úteis no `pyproject.toml`. A licença MIT foi proposta,
  mas nenhum arquivo `LICENSE` foi aplicado. Orbitron e Rajdhani usam SIL OFL 1.1.
- **Verificação:** 601 testes passaram e 1 OpenGL foi ignorado; o smoke de CLI
  e 20 testes headless de partida, dimensões, boss, perfis e cutscenes passaram.
  Ruff passou nos arquivos Python alterados; a varredura global ainda
  registra 177 achados antigos fora do escopo. No benchmark COMIC/MEDIA de
  120 quadros × 5 repetições, duas rodadas por versão, a média/p95 do mundo
  com avanço foi 4,063–4,267/5,290–5,529 ms na main e
  4,079–4,206/5,405–5,615 ms na integração. As faixas se sobrepõem e a
  integração não alterou o desenho do mundo.
- **Bloqueio de CI resolvido:** o mypy apontou dois tipos já existentes no
  controlador de avanço e no indicador de progresso. Foram acrescentados
  `cast` de tipagem, sem conversão de valores nem alteração de regras.
- **Compatibilidade de dados:** um perfil criado pelo código da main anterior
  foi aberto pela integração com identidade, progresso e preferências iguais.
  Um save legado também foi migrado, preservando os bytes de `save.json` e
  `records.json` originais.
- **Ajustes manuais do usuário:** nenhum informado.

## Renomeação final para INCARNATE (1.8.0)

- **Pedido:** consolidar a marca visível, o comando, os atalhos, o executável e
  o instalador; preservar atualização de instalações e dados existentes.
- **Implementação da IA:** pacote e comando `incarnate`, novo `incarnate.py`,
  alias compatível `main.py`, executáveis/artefatos/instalador INCARNATE e
  documentação atualizada. Criados `ROADMAP.md` e `docs/integration-2026-10-18.md`.
- **Decisões:** versão mantida em 1.8.0; AppId Inno Setup preservado;
  `UsePreviousAppDir=yes`; caminhos `VoidShift`/`void-shift` e fallback
  `SPACEFURY_DATA_DIR` permanecem funcionais. Nenhuma migração de dados foi
  necessária. `void-shift` permanece como alias de linha de comando.
- **Verificação:** 602 testes passaram e 1 teste OpenGL foi ignorado; Ruff
  passou nos arquivos Python alterados; `main.py --smoke-test` e
  `incarnate.py --smoke-test` passaram. O benchmark COMIC/MEDIA (1280×720,
  61 entidades, 120 quadros, 3 repetições) marcou média/p95 de 4,771/6,366 ms
  na main e 4,873/6,629 ms nesta branch, com sobreposição de amostras e sem
  alterações no mundo. O cache de marcos ficou em 435.000/610.092/753.200 bytes
  nas qualidades BAIXA/MEDIA/ALTA. PR #27 foi integrado; `v1.8.0-rc1` foi
  publicada como pré-release, e os builds Windows e Linux passaram.
- **Ajustes manuais do usuário:** nenhum informado.
