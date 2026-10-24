# Mundo aberto: design (INCARNATE)

Status: proposta v0. Os valores numéricos são pontos de partida, não promessas: confirmar com benchmark e playtest. As decisões da seção 15 estão confirmadas.

## 1. Objetivo e limites

- Segundo modo de jogo, ao lado do LINEAR. O LINEAR continua idêntico ao atual.
- Protótipo antes do conteúdo completo: 1 região, 1 toca de boss, 3 a 5 destroços, 1 estação, 1 perigo, 1 patrulha.
- Estrutura do mundo em arquivo de dados. Sem dependências novas além do pygame.

## 2. Fluxo de menu

- JOGAR abre uma tela de escolha com dois cartões: LINEAR e MUNDO ABERTO, cada um com descrição curta e o progresso do perfil naquele modo ("Novo" se não houver).
- CONTINUAR retoma o último modo jogado. Esc volta com o foco restaurado.

## 3. Arquitetura

- GameMode (Strategy): LinearMode (código atual, sem mudança) e OpenWorldMode. Interface mínima: iniciar(perfil), atualizar(dt), desenhar(), tratar_evento(), salvar().
- Compartilhados entre os modos: combate, armas, bosses, diálogos, áudio, perfis e o barramento de eventos (BOSS_SPAWNED, BOSS_DEFEATED, GAME_START).
- WorldCamera: segue a nave com suavização e trava na arena do boss.
- WorldMap: carregado de dados e dividido em chunks (1 chunk = 1 tela lógica, 1280x720). Só os 3x3 chunks ao redor da câmera têm entidades ativas. Dos demais guarda-se apenas o estado persistente (coletado, derrotado, descoberto).
- Fundo: o ParallaxBackground recebe o deslocamento da câmera (x e y) em vez de uma velocidade fixa. O ScrollController continua só no LINEAR. Na arena, a "frenagem" é câmera travada e parallax parado (reaproveita o estado PARADO).
- Eventos novos: ECO_COLETADO, TOCA_ENTRADA, ESTACAO_ATIVADA, REGIAO_TROCADA.

## 4. Mapa: decisão

- Opção A: desenhado em dados. Opção B: procedural com semente.
- Recomendação: A para a estrutura (regiões, tocas, estações, destroços), porque controla história e dificuldade. B só para decoração (asteroides, estrelas), com semente fixa por região.

## 5. Regiões

- 6 regiões, uma por dimensão, em grade 3x2 (sugestão):
  - Linha de cima: Nebulosa em Chamas, Floresta de Cristais, Plano Divino.
  - Linha de baixo: Espaço Profundo (início), Oceano Cósmico, Espaço Nulo.
- Tamanho a calibrar pelo tempo: atravessar uma região deve levar cerca de 60 a 90 s de voo.
- Fendas nas fronteiras entre regiões vizinhas (transição visual de cerca de 1 s, reaproveitando a transição dimensional). Plano Divino fica fechado até o boss 5 cair.
- Borda do mapa: o "Vazio" (a imagem se desfazendo) empurra a nave de volta com suavidade, sem parede invisível. Não é o mesmo que a região Espaço Nulo.

## 6. Bosses e tocas

| Boss | Região | Acesso (valores iniciais) |
|---|---|---|
| HEXAGONO | Espaço Profundo | livre |
| LOSANGO | Nebulosa em Chamas | HEXAGONO derrotado + 1 eco |
| ESTRELA | Oceano Cósmico | HEXAGONO derrotado + 2 ecos |
| PENTAGONO | Floresta de Cristais | HEXAGONO derrotado + 3 ecos |
| ANEIS | Espaço Nulo | LOSANGO, ESTRELA e PENTAGONO derrotados + 5 ecos |
| ANEIS DOURADO | Plano Divino | ANEIS derrotado + 7 ecos |

- Os bosses 2, 3 e 4 podem ser feitos em qualquer ordem. Antes de liberar, conferir que as cenas desses capítulos não referenciam umas às outras (hoje não referenciam).
- Meta de conteúdo: pelo menos 7 ecos no mapa completo, com alguns opcionais.
- Toca: estrutura visível de longe que cresce ao se aproximar. A entrada é uma fenda. A arena trava a câmera e freia o fundo, e as cenas pré e pós-boss saem dos eventos existentes, como no LINEAR.
- Vencer o boss "liberta" a região (paleta mais clara, menos perigos).

## 7. Exploração

- Destroços de IAs anteriores guardam um eco (registro corrompido): ao tocar, toca uma cena curta (motor atual, id eco_*) e desbloqueia uma memória no Arquivo, com selo NOVO.
- Cascos abandonados raros (1 por região, opcional) desbloqueiam uma skin.
- Estações: checkpoint e hangar. Viagem rápida entre estações descobertas (fora do protótipo).
- Minibosses patrulham (1 a 2 por região) e reaparecem quando se entra na região de novo.
- Perigos: campo de asteroides (dano de contato), nebulosa (dano gradual), poço de gravidade (puxa a nave). Protótipo: só asteroides.
- Armas achadas no mundo ficam fora do protótipo.

## 8. Navegação

- Radar na borda da tela com marcadores diferenciados por FORMA e cor (toca, estação, destroço descoberto, objetivo). Mostra só o que foi descoberto.
- Seta para o objetivo atual.
- Mapa (tecla M) com névoa por chunk visitado.
- Sem poluir o HUD atual.

## 9. Visual e movimento

- Parallax por posição da câmera (3 a 5 camadas, fatores distintos), marcos grandes com escala por distância, linhas de velocidade na direção do voo proporcionais à velocidade.
- Em qualidade BAIXA, o fundo é estático em cache. "Reduzir efeitos" é respeitado. No máximo 3 flashes por segundo.

## 10. Dados e perfil

- Compartilhado entre modos: skins, memórias (Arquivo), estatísticas gerais e preferências pessoais.
- Por modo: moedas, armas, melhorias, posição/checkpoint, bosses derrotados e tempo de jogo.
- Só do mundo aberto: ecos coletados, chunks visitados, estações descobertas e regiões libertas.
- Migração versionada: no perfil antigo, `modos.linear` recebe os valores atuais e `modos.mundo_aberto` nasce vazio com padrões. Nada se perde. A transferência de perfis inclui os campos novos. Arquivos legados ficam intactos.

## 11. Desempenho (metas iniciais, confirmar medindo)

- Chunks ativos: 3x3. Limite de entidades ativas por qualidade (BAIXA, MEDIA, ALTA) em config.
- Pooling de projéteis e partículas, cache de camadas, sem alocação por frame.
- Medir média e p95 com o benchmark de scroll adaptado, antes e depois.

## 12. Etapas e critérios de aceite

- F1: GameMode e tela de escolha em JOGAR, com o LINEAR idêntico (suíte atual verde e o LINEAR usa o mesmo fluxo de antes).
- F2: câmera e fundo em movimento real num mundo vazio, parallax por posição e borda "Vazio".
- F3: região do protótipo com chunks, radar, 1 perigo, 1 patrulha e 1 estação (checkpoint).
- F4: toca do HEXAGONO com arena, frenagem e cenas pelos eventos existentes, e fenda de entrada.
- F5: destroços e ecos ligados ao Arquivo (selo NOVO), persistência por modo e migração de perfis.
- Cada etapa traz testes da lógica pura: chunks ativos, travas da câmera, requisitos de acesso, migração. O F3 de debug mostra modo, região, chunk, entidades ativas e posição da câmera.

## 13. Riscos

1. Balanceamento sem ordem fixa.
2. Jogador se perder: radar, seta e mapa.
3. Legibilidade de projéteis sobre fundos diferentes.
4. Escopo: protótipo primeiro.
5. Loop atual acoplado ao LINEAR: por isso o F1 vem antes.
6. Conflito com os menus e o kit de UI: só começar depois de A, B e C.

## 14. Critério de sucesso do protótipo

Três pessoas, sem instruções, encontram a toca do boss em até 5 minutos, entendem o radar e não ficam perdidas por mais de 2 minutos.

## 15. Decisões (confirmadas)

1. Mapa: opção A (desenhado em dados). Decoração procedural com semente fixa por região.
2. Ordem dos bosses 2 a 4: livre. Condições: dificuldade equivalente entre os três (ou escalada pelo número de bosses derrotados) e recompensas que não tornem um deles trivial. No mundo aberto, o título do capítulo mostra só o nome (ex.: "// IDENTIDADE"), sem número.
3. Mundo aberto: modo extra ao lado do LINEAR, com o mesmo destaque na tela de escolha. Reavaliar depois do playtest do protótipo.
4. Viagem rápida: fora do protótipo, depois dele.
