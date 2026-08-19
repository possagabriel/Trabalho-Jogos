# Space Fury - Viagem Interdimensional

Shoot 'em up vertical em **Pygame** com progressão, personalização de nave,
6 cenários, inimigos especiais e bosses. O código é 100% procedural
(visual, sons e música são gerados em runtime, sem assets externos).

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
├── requirements.txt      # dependências
├── tests/
│   └── smoke_test.py     # smoke tests headless (sem janela)
├── game/
│   ├── core.py           # Jogo: estado, game loop, combate, HUD, transições
│   ├── config.py         # constantes globais (tela, FPS, cores, limites)
│   ├── settings.py       # Configuracoes: persistidas em data/settings.json
│   ├── player.py         # Jogador, SistemaCombo, catálogo de Skins
│   ├── enemies.py        # Inimigo, InimigoEspecial (sistema de carga), ondas
│   ├── bosses.py         # Boss: 6 bosses, um por cenário, com ataques próprios
│   ├── scenarios.py      # Cenario: gradiente, estrelas, nebulosas e efeitos
│   ├── weapons.py        # ARMARIA (7 armas) e Projetil (inclui ion/feixe)
│   ├── particles.py      # SistemaParticulas, MensagemFlutuante
│   ├── powerups.py       # PowerUp (escudo, vida, arma, velocidade, moedas, skin)
│   ├── shop.py           # LojaSkins: compra/equipa skins (data/skins.json)
│   ├── save_system.py    # SistemaProgressao: save, recordes, estatísticas
│   ├── menu.py           # MenuPrincipal: todas as telas fora do gameplay
│   ├── ui.py             # BotaoNeon e helpers de desenho (HUD, textos, barras)
│   ├── smooth.py         # renderização suave: glow, AA, gradientes, easing
│   ├── theme.py          # paletas NEON/AURORA/MAGMA + utilidades de cor
│   ├── fonts.py          # carregamento das fontes (Orbitron/Rajdhani)
│   ├── geometry.py       # formas geométricas (polígono, estrela, losango...)
│   └── sounds.py         # Sons: efeitos e música gerados proceduralmente
└── data/                 # gerado em runtime (JSON de progresso/config)
```

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

### Níveis e cenários

- `cenario_do_nivel(nivel)` → `min((nivel-1)//5 + 1, 6)`.
- A cada `5` níveis nasce um `Boss` do cenário atual.
- `_transicao_cenario()` executa o "salto dimensional": partículas em
  espiral → flash branco → troca do `Cenario` → revelação.

### Fim de jogo (`_fim_de_jogo`)

Salva recorde, calcula moedas ganhas (bonus por cenário + bosses **da
partida atual**), atualiza estatísticas, sincroniza a loja e vai para
`GAME_OVER`.

---

## Modelo de dados

Tudo é persistido em `data/` como JSON. **Não há banco de dados.**

| Arquivo | Conteúdo |
|---------|----------|
| `save.json` | Progresso: nome, moedas, skins desbloqueadas/atual, total de pontos, bosses, nível máximo, cenários desbloqueados, estatísticas |
| `records.json` | Top 10 recordes (`{nome, pontos, nivel, skin}`) |
| `settings.json` | Configurações: volumes, resolução, tela cheia, sensibilidade, controles, tema |
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

## Testes

```bash
python tests/smoke_test.py     # standalone
pytest tests/ -v               # se pytest estiver instalado
```

Os testes rodam **headless** (drivers dummy do SDL) e cobrem: inicialização,
loop de combate avançando níveis, desenho dos 6 cenários, mapeamento
nível→cenário e a propriedade de atravessar do canhão de íons.