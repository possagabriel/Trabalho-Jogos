# AGENTS.md

Guia para agentes de IA e desenvolvedores trabalharem neste repositório com
segurança. Leia este arquivo antes de alterar qualquer código.

---

## Stack e arquitetura

- **Linguagem:** Python 3.10+ (100% Python).
- **Bibliotecas:** `pygame>=2.5.0` (game loop, SDL), `pytest>=7.0` (testes),
  `ruff>=0.1.0` (lint), `pytest-cov>=4.0` (cobertura). Nada além disso.
- **Arquitetura:** **Hexagonal** (Clean Architecture). Código legado em
  `game/` coexiste com o novo em `src/` enquanto a migração não é concluída.
- **Padrão de jogo:** **Game Loop** clássico. `Application` (`src/core/application.py`)
  inicializa o pygame, mantém o relogio e delega para a `GameContext`
  (máquina de estados) que decide o que é atualizado/desenhado a cada frame.
- **Estado:** máquina de estados (`GameContext` em `src/core/state_machine.py`)
  com estados concretos: `MenuState`, `PlayingState`, `PausedState`,
  `GameOverState`, `LoadingState`. O estado antigo (`Jogo.estado` em
  `game/core.py`) ainda controla o gameplay ativo enquanto a migração
  não termina.
- **Desacoplamento:** `EventBus` singleton (`src/core/event_bus.py`) —
  publicação/inscrição de `GameEvent` por tipo, evitando acoplamento
  direto entre subsystemas.
- **Persistência:** JSON em `data/` (sem banco de dados). Repositório
  abstrato (`src/domain/repository/interface.py`) com implementações
  concretas: `JsonRepository` e `MemoryRepository`.
- **Responsividade:** UI posicionada pelo sistema de layout responsivo de
  `src/infrastructure/ui/layout.py` (ancoras 3x3, containers, proporções,
  safe areas, escala de base 900×700). Legado: `game/layout.py`.
- **Ativos:** código 100% procedural (visual, sons e música gerados em
  runtime), exceto artes em `images/` carregadas por `game/assets.py`.

### Camadas (src/)

| Camada | Pacote | Responsabilidade |
|--------|--------|------------------|
| **Core** | `src/core/` | Application loop, state machine, event bus, constants, settings |
| **Domain** | `src/domain/` | Entidades (Player, Enemy, Boss), sistemas (combat, collision, progression, particles), IA, repositórios |
| **Infrastructure** | `src/infrastructure/` | Graphics (renderer, smooth, cel-shading, theme, fonts), audio (sound_manager), input (commands, controls), persistence (save_manager, serializers), UI (components, hud, layout) |
| **Presentation** | `src/presentation/` | Screens (menu, game, pause, game_over, shop), components (button, label, panel, progress_bar), menu_scene |
| **Shared** | `src/shared/` | Interfaces (Collidable, Renderable, Updatable), types (color, vector), utils (color, math, singleton) |

### Camadas (game/) — legado

| Camada | Módulos | Responsabilidade |
|--------|---------|------------------|
| Núcleo | `core`, `config` | Loop, estados, colisões, pontuação, HUD |
| Entidades | `player`, `enemies`, `bosses`, `weapons`, `powerups` | Objetos com `atualizar()` + `desenhar()` |
| Mundo | `scenarios`, `particles` | Fundo, efeitos, partículas e mensagens |
| Metagame | `shop`, `save_system`, `settings` | Persistência (JSON) e progressão |
| UI | `menu`, `ui`, `theme`, `fonts` | Telas de menu e elementos de interface |
| Visual/Som | `smooth`, `geometry`, `sounds` | Primitivas de desenho/áudio reutilizáveis |

### Padrões de design

- **Singleton:** `EventBus`, `StateManager`
- **Factory:** `EnemyFactory`, `BossFactory`, `ProjectileFactory`
- **Observer:** `EventBus` com `GameEventType`
- **State:** `GameState` → `GameContext` (MenuState, PlayingState, etc.)
- **Command:** Input handling (`MoveUpCommand`, `ShootCommand`, etc.)
- **Strategy:** AI behaviors (`StraightAI`, `ZigZagAI`, `ChaseAI`, etc.)
- **Template Method:** `Entity` base com hooks `before_update`/`after_update`
- **Repository:** `Repository[T]` abstrato → `JsonRepository`, `MemoryRepository`

---

## Estrutura do projeto

```
Trabalho-Jogos/
├── AGENTS.md                # este arquivo
├── CONTRIBUTING.md          # guia de contribuição (inglês)
├── CHANGELOG.md             # histórico de mudanças (Keep a Changelog)
├── README.md                # documentação detalhada do jogo
├── main.py                  # bootstrap legado: ajusta sys.path, chama Jogo()
├── preview_hud.py           # demonstração do HUD em 1920x1080
├── pyproject.toml           # config do projeto (setuptools, ruff, pytest)
├── requirements.txt         # dependências (legado, ver pyproject.toml)
├── .flake8                  # configuração do flake8
├── .pylintrc                # configuração do pylint
├── .gitignore               # ignora __pycache__, .venv/, data/*.json, etc.
├── .gitattributes           # text=auto para data/*.json
├── images/                  # artes de fundo, sprites e logo
├── data/                    # gerado em runtime (JSON; não versionar)
├── tools/
│   └── extract_nave_padrao.py   # utilitário: extrai nave-padrao.png
├── tests/                   # suite de testes (headless)
│   ├── conftest.py          # ambiente headless (SDL dummy) + SPACEFURY_DATA_DIR
│   ├── run_all.py           # suite standalone (sem pytest)
│   ├── smoke_test.py        # smoke test geral
│   └── test_*.py            # testes por módulo
├── game/                    # CÓDIGO LEGADO (sendo migrado para src/)
│   ├── core.py              # Jogo: estado, game loop, combate, HUD
│   ├── config.py            # constantes globais (tela, FPS, cores)
│   ├── assets.py            # caminhos e carregamento das imagens
│   ├── settings.py          # Configuracoes (data/settings.json)
│   ├── player.py            # Jogador, SistemaCombo, Skins
│   ├── enemies.py           # Inimigo, InimigoEspecial, ondas
│   ├── bosses.py            # Entidade RIFT: 6 bosses
│   ├── scenarios.py         # Cenario: gradiente, estrelas, nebulosas
│   ├── weapons.py           # ARMARIA (9 armas) e Projetil
│   ├── particles.py         # SistemaParticulas, MensagemFlutuante
│   ├── powerups.py          # PowerUp (escudo, vida, arma, etc.)
│   ├── shop.py              # LojaSkins
│   ├── save_system.py       # SistemaProgressao
│   ├── menu.py              # MenuPrincipal
│   ├── menu_scene.py        # componentes visuais do menu
│   ├── hud.py               # HUD de combate
│   ├── layout.py            # layout responsivo
│   ├── ui.py                # BotaoNeon e helpers
│   ├── smooth.py            # renderização suave: glow, AA
│   ├── theme.py             # paletas NEON/AURORA/MAGMA
│   ├── fonts.py             # carregamento das fontes
│   ├── geometry.py          # formas geométricas
│   ├── cel_shading.py       # Cel shading / toon shading
│   └── sounds.py            # Sons procedurais
└── src/                     # NOVA ARQUITETURA (hexagonal)
    ├── __init__.py
    ├── core/
    │   ├── application.py   # Application: loop principal, janela, delta_time
    │   ├── constants.py     # Constantes globais (LARGURA, ALTURA, FPS, cores)
    │   ├── event_bus.py     # EventBus singleton + GameEvent/GameEventType
    │   ├── settings.py      # Configuracoes: persistidas em data/settings.json
    │   └── state_machine.py # GameState, GameContext, estados concretos
    ├── domain/
    │   ├── entities/
    │   │   ├── base.py      # Entity (ABC): Template Method com hooks
    │   │   ├── player.py    # Player, Skin, ComboSystem, SKINS catalog
    │   │   ├── enemies/     # Enemy base, behaviors, factory, types/ (shooter, soldier, tank)
    │   │   ├── bosses/      # Boss factory e types
    │   │   └── projectiles/ # ProjectileFactory, ARMARIA
    │   ├── systems/
    │   │   ├── collision_system.py
    │   │   ├── combat.py
    │   │   ├── particle_system.py
    │   │   └── progression.py
    │   ├── ai/              # IA: base, behaviors, enemy_ai
    │   └── repository/      # Repository[T] interface, JsonRepository, MemoryRepository
    ├── infrastructure/
    │   ├── graphics/        # renderer, animation, cel_shading, fonts, geometry, smooth, sprite_factory, theme
    │   ├── audio/           # sound_manager
    │   ├── input/           # commands, controls, input_manager
    │   ├── persistence/     # save_manager, serializers
    │   └── ui/              # components, hud, layout
    ├── presentation/
    │   ├── screens/         # game_screen, game_over_screen, menu_screen, pause_screen, shop_screen
    │   ├── components/      # button, label, panel, progress_bar
    │   └── menu_scene.py    # cenas do menu
    └── shared/
        ├── interfaces/      # collidable, renderable, updatable
        ├── types/           # color, vector
        └── utils/           # color_utils, math_utils, singleton
```

---

## Comandos

### Executar o jogo

```bash
# Instalar dependências
pip install -r requirements.txt          # legado (apenas pygame)
pip install -e ".[dev]"                  # recomendado (instala tudo via pyproject.toml)

# Executar
python main.py                           # via bootstrapper legado
python -m src.core.application           # via novo entry-point (quando disponível)
void-shift                               # se instalado via pip install -e .
```

Sem áudio/vídeo (CI, servidores, debugging):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py
```

### Preview do HUD

```bash
python preview_hud.py            # janela animada
python preview_hud.py --save     # salva images/preview_hud.png
```

### Lint e formatação

```bash
python -m ruff check src/ game/ tests/     # lint rápido (recomendado)
python -m ruff format src/ game/ tests/    # formatação automática
flake8 src/ game/ tests/         # lint alternativo
pylint src/ game/                # análise estática detalhada
```

### Testes

```bash
python -m pytest tests/ # suite completa (recomendado)
python -m pytest tests/ --cov=src # com cobertura de código
python tests/run_all.py # alternativa standalone, sem pytes
```

Os testes rodam **headless** (drivers dummy do SDL, definidos em
`tests/conftest.py`) com um `SPACEFURY_DATA_DIR` temporário. Cada arquivo de
teste também funciona isolado.

---

## Convenções de código

- **Idioma:** Português (nomes, docstrings e comentários). Mantenha assim.
- **Type hints:** obrigatórios em todas as funções públicas.
- **Docstrings:** estilo Google para APIs públicas.
- **Linha:** máximo 100 caracteres (`ruff`, `flake8`, `pylint`).
- **Imports:** dentro de `src/` use absolutos (`from src.core.constants import FPS`); dentro de `game/` use relativos (`from .x import y`).
- **Entidades (src/):** herdam de `Entity` (`src/domain/entities/base.py`), implementam `on_update(dt)` e `render(surface)` via Template Method; retornam eventos novos em `on_update()`.
- **Entidades (game/):** implementam `atualizar(...)` e `desenhar(tela, ...)`; retornam projéteis novos em `atualizar()`.
- **Rect de colisão:** exposto via `get_rect()` (src/) ou `@property rect` (game/), usado com `colliderect`.
- **Configuração:** constantes em `src/core/constants.py` (novo) ou `game/config.py` (legado); config do jogador via `Configuracoes` (`jogo.config["chave"]`).
- **Cores:** base em `constants.py`/`config.py`; destaque por tema via `theme.tema_atual()`. Não use cores RGB soltas.
- **Fontes:** sempre via helpers cacheados. Nunca `pygame.font.Font(None, n)` no meio do jogo.
- **Desenho:** use os helpers de `smooth.py` / `src/infrastructure/graphics/smooth_rendering.py` (`desenhar_glow`, `desenhar_circulo`, etc.) em vez de `pygame.draw.*` direto.
- **UI:** posicione via `layout.py` (nunca coordenadas fixas).
- **Performance:**
  - Superfícies carregadas/cacheadas **nunca devem ser mutadas**; use `.copy()` se precisar alterar `set_alpha`.
  - Não aloque superfícies por frame; reutilize as surfaces de overlay.
  - Cacheie superfícies caras e evite `pygame.draw.*` em loops quentes.

---

## Dependências

- **Verifique antes de adicionar:** se o problema já é resolvido por uma
  biblioteca existente ou por recursos nativos da stdlib/`pygame`, use-os.
  Não adicione dependências desnecessárias.
- **Dependências atuais** (`pyproject.toml`):
  - Runtime: `pygame>=2.5.0`
  - Dev: `pytest>=7.0`, `pytest-cov>=4.0`, `ruff>=0.1.0`
- **Não atualize versões importantes sem verificar compatibilidade.** O jogo
  depende de APIs específicas do `pygame`; subir a versão sem rodar a suite
  completa pode quebrar comportamento silenciosamente.
- Alterações em `requirements.txt` ou `pyproject.toml` exigem rodar a suite
  de testes completa antes de considerar o trabalho pronto.
- Ferramentas de lint configuradas: `ruff` (pyproject.toml), `flake8` (.flake8),
  `pylint` (.pylintrc). Respeite as configurações existentes.

---

## Git

- **NUNCA executar `git reset --hard`** (descarta trabalho e é irreversível).
- Não force push, não faça amend de commits já publicados e não pule hooks.
- **Commits:** seguir Conventional Commits (CONTRIBUTING.md):
  - `feat:` nova feature
  - `fix:` correção de bug
  - `docs:` documentação
  - `style:` formatação
  - `refactor:` reestruturação de código
  - `test:` testes
  - `chore:` manutenção
- Mensagens em **português**, estilo do histórico existente (ex.:
  "feat: menu de pausa interativo com subpainel de configuracoes").
- Antes de commitar: revise `git status`, `git diff` e o histórico recente;
  faça stage apenas dos arquivos intencionais e nunca commite segredos ou
  dados de progresso local (`data/*.json` é ignorado pelo `.gitignore`).

---

## Antes de alterar qualquer código

Sempre:

1. **Procure implementações semelhantes existentes** antes de criar uma nova.
   O projeto tem bastante código pronto tanto em `game/` (legado) quanto em
   `src/` (nova arquitetura). Estenda os catálogos existentes (ex.: dicts
   de `ARMARIA`, `TIPOS`, `CENARIOS`, `SKINS`) em vez de duplicar lógica.
2. **Identifique a camada correta** — entidades ficam em `src/domain/entities/`,
   sistemas em `src/domain/systems/`, infraestrutura técnica em
   `src/infrastructure/`, UI em `src/presentation/`. Não misture camadas.
3. **Identifique os testes existentes** que cobrem a área que você vai mexer
   (a tabela na seção "Testes" do README mapeia arquivo de teste → módulos).
   Rode esses testes antes e depois da sua alteração.
4. Consulte o README (seções "Como estender" e "Convenções do código") e
   CONTRIBUTING.md — eles documentam padrões e processos.
5. Siga o padrão da camada: entidades com `on_update()`/`render()` via
   Template Method (src/) ou `atualizar()`/`desenhar()` (game/), constantes
   em `constants.py`, UI pelo `layout.py`.
6. Ao terminar, rode `pytest tests/` e garanta que a suite completa passa.
