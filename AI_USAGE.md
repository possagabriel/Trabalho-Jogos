# Registro de uso de IA

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
