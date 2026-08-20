# AGENTS.md

## Stack e arquitetura

- **Linguagem:** Python 3 (projeto 100% Python).
- **Bibliotecas:** `pygame-ce` (game loop, SDL) e `pytest` (testes).
- **Padrão:** **Game Loop** clássico. Um estado global (`Jogo.estado` em
  `game/core.py`) decide o que é atualizado e desenhado a cada frame (60 FPS).
- **Estado:** todo o estado do gameplay vive em um único objeto `Jogo`
  (`game/core.py`), referenciado pelos módulos de UI para acessar config,
  progresso, loja e sons.
- **Persistência:** JSON em `data/` (sem banco de dados). Progresso/save,
  recordes, configurações e catálogo de skins.
- **Responsividade:** UI posicionada pelo sistema de layout responsivo de
  `game/layout.py` (ancoras 3x3, containers, proporções, safe areas, escala de
  base 900x700). Nenhum elemento usa coordenada rígida em pixels.
- **Ativos:** código 100% procedural (visual, sons e música gerados em
  runtime), exceto artes de fundo/sprites em `images/` carregadas por
  `game/assets.py` (com fallbacks procedurais).

### Camadas

| Camada | Módulos | Responsabilidade |
|--------|---------|------------------|
| Núcleo | `core`, `config` | Loop, estados, colisões, pontuação, HUD |
| Entidades | `player`, `enemies`, `bosses`, `weapons`, `powerups` | Objetos com `atualizar()` + `desenhar()` |
| Mundo | `scenarios`, `particles` | Fundo, efeitos, partículas e mensagens |
| Metagame | `shop`, `save_system`, `settings` | Persistência (JSON) e progressão |
| UI | `menu`, `ui`, `theme`, `fonts` | Telas de menu e elementos de interface |
| Visual/Som | `smooth`, `geometry`, `sounds` | Primitivas de desenho/áudio reutilizáveis |

---

## Estrutura do projeto

```
Trabalho-Jogos/
├── AGENTS.md            # este arquivo
├── main.py              # bootstrap: ajusta sys.path e chama Jogo().executar()
├── preview_hud.py       # demonstração do HUD em 1920x1080 (janela animada ou --save)
├── requirements.txt     # dependências
├── .gitignore           # ignora __pycache__, .venv/ e data/*.json
├── .gitattributes       # text=auto para data/*.json
├── images/              # artes de fundo, sprites e logo (lidas por game/assets.py)
├── data/                # gerado em runtime (JSON de progresso/config; não versionar)
├── tools/
│   └── extract_nave_padrao.py   # utilitário: extrai nave-padrao.png de naves.png
├── tests/
│   ├── conftest.py      # ambiente headless (SDL dummy) + SPACEFURY_DATA_DIR temporário
│   ├── run_all.py       # suite standalone (sem pytest), arquivo por arquivo
│   ├── smoke_test.py    # smoke test geral (inicialização, níveis, cenários)
│   └── test_*.py        # testes por módulo (ver seção Testes)
└── game/
    ├── __init__.py      # pacote
    ├── core.py          # Jogo: estado, game loop, combate, HUD, transições
    ├── config.py        # constantes globais (tela, FPS, cores, limites)
    ├── assets.py        # caminhos e carregamento das imagens de images/
    ├── settings.py      # Configuracoes: persistidas em data/settings.json
    ├── player.py        # Jogador, SistemaCombo, catálogo de Skins
    ├── enemies.py       # Inimigo, InimigoEspecial (sistema de carga), ondas
    ├── bosses.py        # Entidade RIFT: 6 bosses, um por dimensão
    ├── scenarios.py     # Cenario: gradiente, estrelas, nebulosas, efeitos
    ├── weapons.py       # ARMARIA (9 armas) e Projetil (inclui ion/feixe)
    ├── particles.py     # SistemaParticulas, MensagemFlutuante
    ├── powerups.py      # PowerUp (escudo, vida, arma, velocidade, moedas, skin)
    ├── shop.py          # LojaSkins: compra/equipa skins (data/skins.json)
    ├── save_system.py   # SistemaProgressao: save, recordes, estatísticas
    ├── menu.py          # MenuPrincipal: todas as telas fora do gameplay
    ├── menu_scene.py    # componentes visuais do menu (fundo, HUD, nave)
    ├── hud.py           # HUD de combate (jogador, score, setor, boost, arma, especial, boss)
    ├── layout.py        # layout responsivo: ancoras, containers, proporções, safe areas
    ├── ui.py            # BotaoNeon e helpers de desenho (HUD, textos, barras)
    ├── smooth.py        # renderização suave: glow, AA, gradientes, easing
    ├── theme.py         # paletas NEON/AURORA/MAGMA + utilidades de cor
    ├── fonts.py         # carregamento das fontes (Orbitron/Rajdhani)
    ├── geometry.py      # formas geométricas (polígono, estrela, losango)
    └── sounds.py        # Sons: efeitos e música gerados proceduralmente
```

---

## Comandos

### Executar o jogo

```bash
python -m pip install -r requirements.txt   # primeira vez (pygame-ce, pytest)
python main.py
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

### Testes

```bash
pytest tests/                  # suite completa (recomendado)
python tests/run_all.py        # alternativa standalone, sem pytest
```

Os testes rodam **headless** (drivers dummy do SDL, definidos em
`tests/conftest.py`) com um `SPACEFURY_DATA_DIR` temporário. Cada arquivo de
teste também funciona isolado.

---

## Convenções de código

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
- **UI:** posicione elementos via `game/layout.py` (nunca coordenadas fixas).
- **Docstrings:** todo módulo e classe pública tem docstring curta em
  português explicando responsabilidade.
- **Performance:**
  - Superfícies carregadas/cacheadas **nunca devem ser mutadas**; se precisar
    mudar `set_alpha`, chame `.copy()` primeiro.
  - Não aloque superfícies por frame; reutilize as do `core`
    (`_tela_sombra`, `_tela_flash`, `_tela_fade`).
  - Cacheie superfícies caras e evite `pygame.draw.*` em loops quentes.

---

## Dependências

- **Verifique antes de adicionar:** se o problema já é resolvido por uma
  biblioteca existente ou por recursos nativos da stdlib/`pygame`, use-os.
  Não adicione dependências desnecessárias.
- **Dependências atuais:** apenas `pygame-ce>=2.5` (runtime) e `pytest>=8.0`
  (testes) em `requirements.txt`.
- **Não atualize versões importantes sem verificar compatibilidade.** O jogo
  depende de APIs específicas do `pygame-ce`; subir a versão sem rodar a suite
  completa pode quebrar comportamento silenciosamente.
- Alterações em `requirements.txt` exigem rodar a suite de testes completa
  antes de considerar o trabalho pronto.

---

## Git

- **NUNCA executar `git reset --hard`** (descarta trabalho e é irreversível).
- Não force push, não faça amend de commits já publicados e não pule hooks.
- Commits em **português**, estilo do histórico existente (ex.:
  "Implementa HUD, menu responsivo e expande testes do Space Fury").
- Antes de commitar: revise `git status`, `git diff` e o histórico recente;
  faça stage apenas dos arquivos intencionais e nunca commite segredos ou
  dados de progresso local (`data/*.json` é ignorado pelo `.gitignore`).

---

## Antes de alterar qualquer código

Sempre:

1. **Procure implementações semelhantes existentes** antes de criar uma nova.
   O projeto tem bastante código pronto: armas, inimigos, bosses, cenários,
   skins e efeitos. Estenda os catálogos existentes (ex.: dicts de `ARMARIA`,
   `TIPOS`, `CENARIOS`, `SKINS`) em vez de duplicar lógica.
2. **Identifique os testes existentes** que cobrem a área que você vai mexer
   (a tabela na seção "Testes" do README mapeia arquivo de teste → módulos).
   Rode esses testes antes e depois da sua alteração.
3. Consulte o README (seções "Como estender" e "Convenções do código") — ele
   documenta o passo a passo para adicionar arma, inimigo, cenário e skin.
4. Siga o padrão da camada: entidades com `atualizar()`/`desenhar()`,
   constantes em `config.py`, UI pelo `layout.py`.
5. Ao terminar, rode `pytest tests/` e garanta que a suite completa passa.