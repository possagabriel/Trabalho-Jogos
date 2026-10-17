# Registro de uso de IA

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
