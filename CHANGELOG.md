# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Versão sugerida para os minibosses: **1.2.0** (nova funcionalidade compatível).

### Added
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
