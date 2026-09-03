# VOID//SHIFT - Enter the Rift

Shoot 'em up vertical em **Pygame** com progressão, personalização de nave,
6 dimensões, inimigos especiais e entidades RIFT (bosses). O código é 100%
procedural (visual, sons e música são gerados em runtime, sem assets
externos).

> Este README é orientado a **desenvolvedores e IAs**: explica a arquitetura,
> o fluxo de dados e as convenções para que qualquer pessoa (ou modelo) possa
> navegar, modificar e estender o código com segurança.

---

## Sumário

1. [Como executar](#como-executar)
2. [Arquitetura](#arquitetura)
3. [Fluxo do jogo](#fluxo-do-jogo)
4. [Modelo de dados](#modelo-de-dados)
5. [Convenções do código](#convenções-do-código)
6. [Performance](#performance)
7. [Como estender](#como-estender)
8. [Testes](#testes)

---

## Como executar

```bash
python -m pip install -r requirements.txt   # pygame-ce
python main.py
```

Sem áudio/vídeo (CI, servidores, debugging):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py
```

### Resolução e responsividade

O jogo renderiza numa superfície interna de **900×700** e a ajusta à janela
preservando a proporção (scale-to-fit). O posicionamento de **toda** a UI passa
pelo módulo `game/layout.py` — um sistema responsivo com **ancoras** (grade
3x3), **containers** ancorados, **proporções** da superfície, **escala** de uma
base de design (900×700) e **safe areas** (margem interna). Nenhum elemento usa
coordenada rígida em pixels: se a superfície lógica mudar de tamanho, o menu se
recompõe automaticamente.

- **Resoluções suportadas:** `900x700`, `1024x768`, `1280x720`, `1280x800`,
  `1366x768`, `1440x900`, `1600x900`, `1680x1050`, `1920x1080`, `2560x1080`,
  `2560x1440`, `3440x1440`, `3840x2160` (a lista vive em `settings.RESOLUCOES`;
  no menu **Config → Resolução** há um seletor com rolagem para escolher).
- **Modo de aspecto** (configuração `aspecto`, disponível em Settings):
  - `AJUSTAR` (padrão): *scale-to-fit* com **safe areas** (letterbox) em
    `VOID_BLACK`, mantendo proporções iguais em qualquer formato de tela.
  - `PREENCHE`: estica a cena para preencher a janela inteira.
- **Tela cheia:** usa a resolução nativa do monitor (sem `SCALED`, sem esticar).
- **Ajustar Tela** (Config → Ajustar Tela): calibra a imagem para o monitor
  (TVs com overscan, telas com bordas cortadas etc.). Com setas move a imagem
  (4 px por passo), `W/S` aplica zoom (0.9–1.2), `R` reseta e `Enter` confirma
  (ou `Esc` cancela). Persistido em `ajuste_escala`, `ajuste_off_x` e
  `ajuste_off_y`; vale tanto no modo `AJUSTAR` quanto no `PREENCHE`.
- **Conversão do mouse:** `MenuPrincipal._pos_logica` converte coordenadas da
  janela para a superfície interna aplicando a transformação vigente (escala +
  offsets do letterbox e os ajustes manuais de Ajustar Tela; proporção direta
  com escala no modo `PREENCHE`).
- **Layout responsivo:** `game/layout.py` define `Layout`, com `x()/y()`
  (frações da superfície), `px()` (escala da base de design), `rect(ancora, …)`
  (containers), `ponto(ancora, …)` e `fonte(...)` (fontes escaladas). Todas as
  telas do menu (`menu.py`) e os elementos visuais (`menu_scene.py`) derivam
  suas geometrias dele.

---

## Arquitetura

O projeto segue o padrão **Game Loop** clássico: um estado global
(`Jogo.estado`) decide o que é atualizado e desenhado a cada frame. Todo o
estado do gameplay vive em **um único objeto `Jogo`** (`game/core.py`),
que é referenciado pelos módulos de UI quando precisam acessar config,
progresso, loja e sons.

```
space_fury/
├── main.py               # bootstrap: ajusta sys.path e chama Jogo().executar()
├── preview_hud.py        # demonstração do HUD em 1920x1080 (janela animada ou --save)
├── requirements.txt      # dependências
├── images/               # artes de fundo e sprites (carregadas por game/assets.py)
├── tests/
│   └── smoke_test.py     # smoke tests headless (sem janela)
├── game/
│   ├── core.py           # Jogo: estado, game loop, combate, HUD, transições
│   ├── config.py         # constantes globais (tela, FPS, cores, limites)
│   ├── assets.py         # caminhos e carregamento das imagens de images/
│   ├── settings.py       # Configuracoes: persistidas em data/settings.json
│   ├── player.py         # Jogador, SistemaCombo, catálogo de Skins
│   ├── enemies.py        # Inimigo, InimigoEspecial (sistema de carga), ondas
│   ├── bosses.py         # Entidade RIFT: 6 bosses, um por dimensão, com ataques próprios
│   ├── scenarios.py      # Cenario: gradiente, estrelas, nebulosas e efeitos
│   ├── weapons.py        # ARMARIA (9 armas) e Projetil (inclui ion/feixe)
│   ├── particles.py      # SistemaParticulas, MensagemFlutuante
│   ├── powerups.py       # PowerUp (escudo, vida, arma, velocidade, moedas, skin)
│   ├── shop.py           # LojaSkins: compra/equipa skins (data/skins.json)
│   ├── save_system.py    # SistemaProgressao: save, recordes, estatísticas
│   ├── menu.py           # MenuPrincipal: todas as telas fora do gameplay
│   ├── menu_scene.py     # componentes visuais do menu (fundo, HUD, nave…)
│   ├── hud.py            # HUD profissional de combate (jogador, score, setor, boost, arma, especial, boss)
│   ├── layout.py         # layout responsivo: ancoras, containers, proporções, safe areas
│   ├── ui.py             # BotaoNeon e helpers de desenho (HUD, textos, barras)
│   ├── smooth.py         # renderização suave: glow, AA, gradientes, easing
│   ├── theme.py          # paletas NEON/AURORA/MAGMA + utilidades de cor
│   ├── fonts.py          # carregamento das fontes (Orbitron/Rajdhani)
│   ├── geometry.py       # formas geométricas (polígono, estrela, losango...)
│   └── sounds.py         # Sons: efeitos e música gerados proceduralmente
└── data/                 # gerado em runtime (JSON de progresso/config)
```

### Ativos visuais

A pasta `images/` concentra as artes: fundos por cenário, o menu e a folha de
sprites de naves (`naves.png`). A nave padrão do jogador é um recorte da folha
(`nave-padrao.png`, extraído com fundo transparente) e é carregada por
`game/player.py` com fallback para a nave procedural caso o arquivo falte.

### Responsabilidades por camada

| Camada | Módulos | Responsabilidade |
|--------|---------|------------------|
| **Núcleo** | `core`, `config` | Loop, estados, colisões, pontuação, HUD |
| **Entidades** | `player`, `enemies`, `bosses`, `weapons`, `powerups` | Objetos com `atualizar()` + `desenhar()` |
| **Mundo** | `scenarios`, `particles` | Fundo, efeitos, partículas e mensagens |
| **Metagame** | `shop`, `save_system`, `settings` | Persistência (JSON) e progressão |
| **UI** | `menu`, `ui`, `theme`, `fonts` | Telas de menu e elementos de interface |
| **Visual/Som** | `smooth`, `geometry`, `sounds` | Primitivas de desenho/áudio reutilizáveis |

---

## Fluxo do jogo

### Estados (`Jogo.estado`)

`MENU`, `CONTINUAR`, `LOJA`, `RECORDES`, `CONFIG` → renderizados pelo
`MenuPrincipal`. Durante o gameplay: `PREPARANDO` (tela de carregamento
falsa) → `JOGANDO` → `PAUSA` / `GAME_OVER`.

### Loop principal (`core.Jogo.executar`)

A cada frame, na ordem:

1. `_tratar_eventos()` — eventos do SDL (teclado, mouse, sair).
2. `_atualizar()` — avança o estado do mundo conforme `self.estado`.
3. `_desenhar()` — desenha o cenário atual + HUD + overlays.
4. `relogio.tick(FPS)` — trava a 60 FPS.

### Combate (`_atualizar_jogando`)

1. Lê o teclado e move/atira (`Jogador.atualizar` / `atirar`).
2. Faz **spawn** de inimigos da `fila_onda` (1 a cada ~35 frames).
3. Atualiza todos os inimigos (movimento + ataques geram projéteis).
4. `_atualizar_projeteis()` — move, colide e aplica dano.
5. `_atualizar_powerups()` — coleta e aplica efeitos.
6. Se não há onda/inimigos/boss → `_iniciar_nivel(nivel + 1)`.

### Níveis e dimensões

- `cenario_do_nivel(nivel)` → `min((nivel-1)//5 + 1, 6)`.
- A cada `5` níveis nasce uma **entidade RIFT** (boss) da dimensão atual.
- `_transicao_cenario()` executa o "salto dimensional": partículas em
  espiral → flash branco → troca da `Dimensao` → revelação.

### Fim de jogo (`_fim_de_jogo`)

Salva recorde, calcula moedas ganhas (bonus por dimensão + entidades RIFT **da
partida atual**), atualiza estatísticas, sincroniza a loja e vai para
`GAME_OVER`.

---

## Modelo de dados

Tudo é persistido em `data/` como JSON. **Não há banco de dados.**

| Arquivo | Conteúdo |
|---------|----------|
| `save.json` | Progresso: nome, moedas, skins desbloqueadas/atual, total de pontos, bosses, nível máximo, cenários desbloqueados, estatísticas |
| `records.json` | Top 10 recordes (`{nome, pontos, nivel, skin}`) |
| `settings.json` | Configurações: volumes, resolução, tela cheia, sensibilidade, controles, tema, aspecto |
| `skins.json` | Catálogo de skins (criado na primeira execução, espelha `player.SKINS`) |

**Fluxo de gravação:** `MenuPrincipal`/`Jogo` mutam os objetos em memória
(loja, config, progresso) e chamam `_salvar_tudo()` /
`config.salvar()` que serializam em disco. `SistemaProgressao.sincronizar_loja`
garante que moedas/skins da `LojaSkins` sejam espelhadas no save.

---

## Convenções do código

- **Idioma:** Português (nomes, docstrings e comentários). Mantenha assim.
- **Imports:** sempre relativos dentro do pacote `game` (`from .x import y`).
- **Estrutura de entidades:** cada entidade (inimigo, boss, projétil, power-up)
  implementa `atualizar(...)` e `desenhar(tela, ...)`; retorna projéteis novos
  a partir de `atualizar()` para o `core` adicionar às listas.
- **Rect de colisão:** exposto via `@property rect` (retângulo centrado no
  raio), usado com `colliderect`.
- **Configuração:** constantes globais em `config.py`; configurações do
  jogador via `Configuracoes` (acessadas por `jogo.config["chave"]`).
- **Cores:** cores base em `config.py`; cores de destaque por tema via
  `theme.tema_atual()`. Não use cores RGB soltas espalhadas pelo código.
- **Fontes:** sempre via `fonte_texto(tamanho)` / `fonte_titulo(tamanho)`
  (cacheadas). Nunca `pygame.font.Font(None, n)` no meio do jogo.
- **Desenho:** use os helpers de `smooth.py` (`desenhar_glow`,
  `desenhar_circulo`, `desenhar_poligono`, `desenhar_painel`) em vez de
  `pygame.draw.*` direto — eles dão AA/glow e usam cache.
- **Docstrings:** todo módulo e classe pública tem docstring curta em
  português explicando responsabilidade.

---

## Performance

O jogo roda a 60 FPS; as regras abaixo mantêm isso:

1. **Superfícies carregadas/cacheadas nunca devem ser mutadas.**
   `luz_radial`, `circulo_suave`, `texto_suave` etc. retornam objetos do
   cache. Se você precisar mudar `set_alpha`, chame `.copy()` primeiro
   (ver `particles.Particula.desenhar` e `scenarios._desenhar_efeito`).
2. **Não aloque superfícies por frame.** Reutilize `self._tela_sombra`,
   `_tela_flash` e `_tela_fade` do `core` para overlays.
3. **Cacheie superfícies caras.** Ex.: `_CACHE_RAIOS` em `scenarios.py`
   evita recriar os raios de luz a cada frame.
4. **Evite `pygame.draw.*` em loops quentes**; prefira `smooth.*` (cacheado).
5. **Supersampling** (`_SCALA_AA`) já é aplicado em polígonos/retângulos —
   não re-renderize na mão.
6. Fontes são cacheadas por tamanho em `fonts.py`.

---

## Como estender

### Nova arma
1. Adicione um dict em `ARMARIA` (`game/weapons.py`) com `nivel`, `cor`,
   `raio`, `vel`, `dano`, `cooldown`, `tipo`.
2. Implemente o disparo em `Jogador.atirar` (novo branch de `tipo`).
3. Se o projétil tiver comportamento visual novo, adicione um `tipo` em
   `Projetil.desenhar`.

### Novo inimigo
1. Adicione o tipo em `TIPOS` e a forma em `FORMAS` (`game/enemies.py`).
2. Implemente o movimento em `Inimigo.atualizar` e o ataque em `_atacar`.
3. Inclua o tipo na lista `inimigos` de um cenário em `scenarios.py`.

### Novo inimigo especial
1. Adicione entradas em `CARGA_POR_TIRO`, `CORES` e no dict de `base`/
   `mov` em `InimigoEspecial`.
2. Implemente a ação ao carregar em `acoes_carregado` e o desenho em
   `desenhar`.

### Novo cenário
1. Adicione um dict em `CENARIOS` (`scenarios.py`) — cores, camadas de
   estrelas, efeito, inimigos, especiais.
2. Se o efeito for novo, implemente em `Cenario._atualizar_efeito` /
   `_desenhar_efeito`.
3. Adicione o boss correspondente em `BOSSES_POR_CENARIO` (`bosses.py`).

### Nova skin
1. Adicione um dict em `SKINS` (`player.py`) com `id`, `preco`, `cor`,
   `efeito`, `descricao`.
2. Implemente o efeito visual em `Skin.desenhar`/`_desenhar_*`.

---

## HUD de combate

O HUD fica em `game/hud.py` (`HudJogo`) e é desenhado pelo core em
`_desenhar_hud()`. É **responsivo** (usa `game/layout`, escala de
1920x1080 até janelas menores) e mantém o **centro da tela sempre livre**
para o gameplay. O **tom do HUD acompanha a fase**: cada dimensão tinge
os painéis, o badge do jogador, boost, energia e a barra de especial com
as cores principais do cenário (`cores_principais` em `scenarios.py`;
sem elas usa a paleta padrão da marca ciano/magenta):

| Módulo | Posição | Conteúdo |
| --- | --- | --- |
| Jogador | topo-esquerda | ícone da nave, `PLAYER 01`, vida segmentada + numérica, escudo (ciano), energia |
| Score | topo-direita | `SCORE` grande, `HIGH SCORE`, abates, multiplicador combo |
| Setor | topo-centro | `SECTOR xx`, nome da região e barra de progresso da fase (discreta) |
| Boost | base-esquerda | medidor circular com ticks, velocidade |
| Arma | base-direita | ícone geométrico da arma, nome, `LVL`, carga/munição |
| Especial | base-centro | barra de especial com `SPECIAL READY` pulsando quando cheia (tecla `E`) |
| Boss | topo-centro | barra dourada segmentada com nome (só aparece com chefe em tela) |

Os medidores novos (`boost`, `especial`, `energia`) são mantidos pelo core:
SHIFT/LCTRL turbina (drena boost e energia), abates carregam o especial.

Para ver todos os componentes sobre um fundo neutro em 1920x1080:

```bash
python preview_hud.py            # janela animada
python preview_hud.py --save     # salva images/preview_hud.png
```

---

## Testes

```bash
pytest tests/                  # suite completa (recomendado)
python tests/run_all.py        # alternativa standalone, sem pytest
```

Os testes rodam **headless** (drivers dummy do SDL). O `tests/conftest.py`
define o ambiente antes de qualquer importação do jogo e cria um
`SPACEFURY_DATA_DIR` temporário para a sessão do pytest; cada arquivo também
funciona isolado. Cobertura por módulo:

| Arquivo | Módulos | O que cobre |
| --- | --- | --- |
| `test_theme_geometry_smooth.py` | theme, geometry, smooth | cores (mix, ciclo, esmaecer), easing, caches e desenho suave (glow, gradientes, painéis, textos) |
| `test_settings_save_shop.py` | settings, save_system, shop | configurações, persistência de progresso/save e loja de skins |
| `test_weapons_powerups.py` | weapons, powerups | todos os tipos de projétil (laser, ion, gauss, espiral...) e power-ups (vida, escudo, arma, skin...) |
| `test_player.py` | player | jogador: movimento, controles, cooldowns, rajadas, combo, dano, skins (inclui sprite da nave padrão e fallback) |
| `test_enemies_bosses.py` | enemies, bosses | inimigos, especiais (acumulador, cristalino...), ondas, sorteios e todos os bosses |
| `test_scenarios_particles.py` | scenarios, particles | 6 cenários, estrelas, cover, partículas e mensagens flutuantes |
| `test_menu_scene.py` | menu_scene | fundo com `fundo-menuprincipal.png` (e fallback), HUD, nave, destaque, transições |
| `test_menu.py` | menu | menu principal: construção, navegação entre telas, save, loja, diálogo de saída, `_pos_logica` |
| `test_interacao.py` | core, menu | eventos reais (pygame.event): teclas de navegação, pausa/game over, remap de controles e cliques do mouse |
| `test_core.py` | core | estados, níveis/boss a cada 5, desbloqueio de armas, combate e fim de jogo |
| `test_hud.py` | hud | HUD: renderização de todos os módulos, segmentos, barra de boss, medidores e duck typing |
| `test_layout.py` | layout | layout responsivo nas resoluções-alvo |

O `smoke_test.py` faz um smoke test geral: inicialização, loop de combate
avançando níveis, desenho dos 6 cenários e mapeamento nível→cenário.