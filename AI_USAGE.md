# Registro de uso de IA

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
