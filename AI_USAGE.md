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
