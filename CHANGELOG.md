# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- AGENTS.md consolida escopo de leitura, fluxo Git, validação, acessibilidade e regras de roteiro do INCARNATE.
- O menu ganhou cartão de perfil alimentado pelo `ProfileService`, resumo real
  do ponto inicial de Continuar e selos persistentes para Memórias e itens do
  Hangar que ficaram compráveis. O schema de perfil migra automaticamente para v3.
- ORIGINAL e COMIC usam a mesma hierarquia e uma composição própria para janelas
  próximas de 4:3. Rótulos de telemetria sem dados reais saíram do HUD decorativo.
- O saldo do rodapé agora vem do perfil ativo, igual ao cartão de perfil.
- Menu ORIGINAL e COMIC compartilham cinco destinos: Jogar, Hangar, Perfil,
  Configurações e Sair; os hubs de Jogar e Perfil preservam os callbacks atuais
  e deixam cada tela anterior acessível em até duas ações.
- O perfil versionado guarda os IDs de novidades reconhecidas no Arquivo e no
  Hangar, com defaults para perfis antigos e transferência preservada.
- Um perfil recém-criado sem partidas não é tratado como save continuável; o
  resumo de Continuar mostra a partida iniciada na Dimensão 1 / Nível 1.
- README documenta a navegação nova, os destinos de Lobby/Hangar e a ausência
  de retomada por checkpoint.
- A nave foi reposicionada para equilibrar o título e a coluna de ações. O marcador
  de seleção e os painéis estáticos usam superfícies em cache.
- O título recebe pulsos cromáticos breves em vez de glitch contínuo; a opção de
  intensidade de flashes reduz ou desliga esses pulsos.
- O README inclui capturas otimizadas do menu ORIGINAL em 1920×1080 e ultrawide.

### Fixed
- Menu lê sua versão de `project.version` no `pyproject.toml`.
- Menu ORIGINAL mantém títulos, botões e textos de rodapé dentro das margens,
  com contraste reforçado, rótulos ajustáveis e Continue desabilitado sem save.
- O rodapé trunca nomes longos sem alterar perfis existentes; a validação atual
  continua rejeitando apóstrofos em nomes novos e renomeações.

### Added
- Licença MIT do projeto e avisos OFL 1.1 de Orbitron e Rajdhani nos pacotes.
- README resume o aviso SmartScreen/antivírus e a verificação SHA-256.

### Fixed
- Fallback de OpenGL reinicializa o subsistema de vídeo antes de criar a janela
  CPU quando a criação do apresentador GPU falha.

## [1.8.0] - 2026-10-18

### Changed
- Produto, pacote Python, comando principal, ponto de entrada, executável,
  artefatos e instalador agora usam o nome INCARNATE. `void-shift`, `main.py` e
  os diretórios de dados anteriores continuam compatíveis.
- O AppId do Inno Setup foi mantido para atualizar instalações existentes; a
  candidata usa metadados de pré-lançamento sem marcar a release como latest.
- Contornos de sprites escalam com o tamanho, respeitando limites comuns para
  nave, inimigos, bosses e skins.
- Densidade de hachura cresce com o tamanho do sprite e é omitida nas formas pequenas,
  mantendo detalhes visuais legíveis sem alterar hitboxes.
- Screenshot do README registra as dez skins COMIC em quatro direções.
- Versão do projeto elevada de 1.7.0 para 1.8.0.
- README reorganizado em guia para jogadores e documentação técnica, com descrição
  correta dos assets, resolução interna, controles, fases e cobertura de testes.
- Ruff centralizado em `pyproject.toml`; scripts de dados usam o caminho canônico
  `INCARNATE_DATA_DIR` e preservam `SPACEFURY_DATA_DIR` como fallback legado.
- Preview do HUD movido para `tools/`; CI de qualidade dispara em qualquer push e PR.
- Guia de migração atualizado com os módulos pendentes e critérios para remover `game/`.

## [1.7.0] - 2026-10-18

### Changed
- Fundos COMIC agora usam composição distinta para cada dimensão: rotas orbitais,
  cristas vulcânicas, ondas e recifes, cristais, fendas e raios divinos.
- Detalhes de fundo têm menos densidade, contraste e saturação para preservar a leitura
  de inimigos, projéteis e marcos.
- Projéteis inimigos usam contorno escuro e claro com contraste mínimo de 3:1; hitboxes
  e lógica de combate não mudam.
- Screenshot do README documenta as seis composições de cenário.
- Versão do projeto elevada de 1.6.0 para 1.7.0.

## [1.6.0] - 2026-10-18

### Added
- Marcos procedurais de percurso por dimensão, com sorteio reproduzível, pool
  limitado por qualidade, evolução visual e destino de chegada para bosses.
- Progresso de nível suavizado, monotônico e visível no F3, junto da semente e
  da agenda de marcos.
- Opções globais para marcos, evolução visual e ritmo variável, compatíveis com
  `settings.json` antigos.

### Changed
- `PREENCHE` preserva a área jogável em 16:9 e estende somente o fundo decorativo.
- Configurações e README explicam que as bordas adicionais não ampliam o campo de jogo.
- Flash e fade de transição também cobrem as faixas decorativas; a apresentação reutiliza
  buffers de escala e de fundo, e as bordas ficam fora do shake da câmera.
- HUD renderizado na resolução física da área jogável, com tipografia mínima efetiva,
  contraste automatizado e cores/medidas centralizadas em tokens.
- Medidor circular do HUD desenhado sem superfície temporária por quadro; brilho removido
  de elementos não focados.
- Fundos rasterizados de cutscene recebem acabamento cartoon pré-processado e cacheado,
  com posterização, tinta de dimensão, contorno e retícula.
- Caixa de diálogo, retratos, títulos e controles de cutscene usam contorno cartoon sem
  glow decorativo; magenta fica restrito aos glitches e alertas.
- A troca de dimensão faz fade dos marcos antigos e novos sem alterar a
  transição de combate existente.
- Versão do projeto elevada de 1.5.0 para 1.6.0.

## [1.5.0] - 2026-10-18

### Added
- Perfis locais com UUID, seleção inicial, criação, renomeação e exclusão confirmada.
- Progresso, recordes, preferências de mira e controles separados por perfil.
- Repositório JSON versionado com backups, recuperação de índice e aviso para perfis danificados.
- Migração idempotente do save único, preservando `save.json` e `records.json` originais.
- Indicadores do perfil, última gravação e alterações pendentes no overlay F3.
- Importação e exportação portáteis pela CLI sem novas gravações nos arquivos legados.

### Changed
- Melhorias de partida são contadas por perfil como estatísticas; seus efeitos continuam
  restritos à partida atual.
- `settings.json` mantém somente opções globais; controles, sensibilidade e mira ficam
  no perfil selecionado.
- Versão do projeto elevada de 1.4.0 para 1.5.0.

## [1.4.0] - 2026-10-17

### Added
- Motor de cutscenes em JSON com diálogo progressivo, fades, glitch, shake,
  retratos cacheados, áudio e títulos; capítulo 1 e introdução para revisão.
- Arquivo de Memórias para rever cenas vistas e seletor F3 + F8 para depuração.
- `cenas_vistas` retrocompatível no save e velocidade do diálogo no settings.

### Changed
- Combate congela durante cenas; avanço aguarda o pós-boss antes de acelerar.
- Aberturas de dimensão começam após a transição visual existente.
- Versão do projeto elevada de 1.3.0 para 1.4.0.

## [1.3.0] - 2026-10-17

### Added
- Sprites direcionais em cache para as dez skins; a nave acompanha a mira sem
  alterar a hitbox, preservando poses e efeitos visuais.
- Rolagem contínua 2D com fundos sem emenda, parallax de 3 a 5 camadas e linhas
  de velocidade para as seis dimensões nos estilos ORIGINAL e COMIC.
- Frenagem ao entrar um boss, avanço residual distante durante a luta,
  aceleração após a derrota e impulso durante o salto dimensional existente.
- Desaceleração de minibosses a 50% por padrão, com ajuste geral e por tipo.
- Configurações persistidas de direção, velocidades, qualidade, camadas,
  linhas, intensidade e duração; overlay F3 com estado e velocidade do avanço.
- Eventos genéricos publicados na entrada e derrota de bosses para reutilização
  futura por outros sistemas.
- Testes da máquina de estados e integração e benchmark de 61 entidades.

### Changed
- O brilho do propulsor acompanha a velocidade visual do cenário.
- Versão do projeto elevada de 1.2.0 para 1.3.0.

## [1.2.0] - 2026-10-17

### Added
- Combo por acertos com expiração temporal; Íon e Gauss atingem cada alvo uma
  vez por projétil.
- Transição dimensional atualizada pelo loop principal, com eventos responsivos.
- Tutorial contextual da primeira partida e módulos entre setores com custos.
- Controles de flash, tremor e hitbox; projéteis hostis destacados e fundo
  escurecido em encontros intensos.
- Mira cartoon por dimensão com pulso de disparo, feedback sobre inimigos,
  toggle persistente e controle de tiro pelo mouse com fallback de teclado.
- Overlay F3 com FPS, posição da mira, hitboxes e contagem de camadas ativas.
- Shader GPU opcional para o estilo comic, com posterização, detecção de bordas
  Sobel, hachuras por perfil, grão e controle de intensidade em tempo real.
- Estado e controles do shader no menu, com fallback automático para a
  apresentação OpenGL sem filtro ou para o renderizador de CPU.
- Caminho moderno GLSL 3.30 com VBO/VAO e fallback GLSL 1.20, posterização por
  luminância, hachuras/grão estáveis e controles de contorno, tons e saturação.
- Composição separada de mundo e interface para preservar HUD, menus e textos;
  teste OpenGL real automatizado com Mesa no CI.
- Sete minibosses corporativos: Bastião, Espectro, Matriz, Censor, Cartógrafo,
  Eco e Cronista, com escudo por núcleos, teleporte, lacaios, inversão de
  movimento, zonas de perigo, cópia de disparos e ciclos de invulnerabilidade.
- Spawner por ondas ou segundos de simulação, pesos e dimensões configuráveis,
  RNG com seed, proteção contra repetição e limite de um miniboss ativo.
- Registry/Factory, estratégias e estados de aviso/ataque/recuperação;
  integração com colisões, armas, HUD, pausa, progressão e reinício.
- Contagem total e por tipo em saves antigos, com recompensa persistida uma
  única vez e sem interferência na progressão dos bosses principais.
- Testes headless do sistema e guia de extensão/balanceamento em `docs/minibosses.md`.
- Hexagonal architecture with clear separation of concerns
- Design patterns: Singleton, Factory Method, Observer, State, Command, Strategy, Template Method
- Event bus system for decoupled communication
- State machine for game state management
- Command pattern for input handling
- Strategy pattern for enemy AI behaviors
- Factory pattern for entity creation (enemies, bosses, projectiles)
- Template method pattern for entity base classes
- Repository pattern for data persistence
- Responsive layout system
- Cel shading / toon shading rendering pipeline
- Procedural audio system
- Professional HUD with segmented bars and gauges
- Particle system with 17+ effects
- Skin shop with 10 skins
- 6 dimensional scenarios with unique visuals
- 15 enemy types with 6 special variants
- 6 boss types (one per dimension)
- 9 weapon types with distinct behaviors
- Combo scoring system
- Save/records persistence in JSON

### Changed
- Catálogo e efeitos dos módulos movidos para o domínio; animação dimensional
  isolada na apresentação e escalas visuais compartilhadas pela configuração.
- Disparos direcionais apontam para a mira; Duplo e Espiral mantêm dispersão
  configurável em `settings.json`. O Íon conserva a coluna vertical.
- O shader foi refatorado em fontes GLSL isoladas, opções imutáveis e validadas,
  catálogo único de controles e uma única rotina de composição GPU.
- O Lobby de fases agora usa fundo, lettering, miniaturas e painéis do estilo
  comic, mantendo o visual legado quando o jogador seleciona ORIGINAL.
- O workflow do instalador Windows agora usa a versão da tag ou do projeto,
  valida os binários e publica somas SHA-256 junto dos artefatos.
- Menus secundários e telas de confirmação passaram a usar o mesmo painel
  angular, borda e tipografia do menu principal.
- Maior espaçamento entre as opções do menu principal, eliminando sobreposição
  das áreas de clique e reposicionando o rodapé conforme o layout responsivo.
- Restructured codebase into src/ package with hexagonal architecture
- Separated domain logic from presentation and infrastructure
- Extracted combat, progression, and collision into dedicated systems
- Moved rendering utilities to infrastructure/graphics
- Moved input handling to infrastructure/input with Command pattern
- Moved UI components to infrastructure/ui

### Fixed
- A loja do Lobby passou a usar a mesma carteira do Hangar, reverte a cobrança
  se o save falhar e aplica de fato blindagem e motor comprados à nova partida.
- Derrotar a Matriz remove os lacaios das consultas de colisão no mesmo quadro,
  evitando recompensas indevidas e falha ao processar tiros ou explosões restantes.

## [1.1.0] - 2026-09-18

### Added
- Estilo comic original: tinta, materiais chapados, hachuras, papel e halftone.
- Pipeline de posterização, máscaras e contornos em cache, com banking pré-calculado.
- Fundos procedurais, bursts, traços de velocidade, lettering e painéis angulares.
- Números de dano normal, crítico e elemental; raridade visual no HUD das armas.
- Perfis comic BAIXA/MEDIA/ALTA, toggles independentes e tremida opcional dos contornos.
- Preview reproduzível, benchmark por componente e documentação em `docs/visual/README.md`.
- Testes de cache, configuração, transparência, fallback e replay entre estilos.

### Changed
- COMIC como estilo padrão; ORIGINAL pode ser selecionado nas configurações.
- Renderização delega aos helpers de infraestrutura sem alterar regras de combate,
  colisões, movimento, controles, catálogo de atributos ou formato de progresso.
- Fontes padrão de efeitos passam a ser reutilizadas em cache.

## [1.0.0] - 2026-08-21

### Added
- Initial release of INCARNATE
- Complete game with 6 dimensions, 15 enemies, 6 bosses
- 9 weapons, 10 skins, particle system
- Cel shading visual style
- Procedural audio
- Save/records system
