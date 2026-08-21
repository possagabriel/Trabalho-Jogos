# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- Restructured codebase into src/ package with hexagonal architecture
- Separated domain logic from presentation and infrastructure
- Extracted combat, progression, and collision into dedicated systems
- Moved rendering utilities to infrastructure/graphics
- Moved input handling to infrastructure/input with Command pattern
- Moved UI components to infrastructure/ui

## [1.0.0] - 2026-08-21

### Added
- Initial release of VOID//SHIFT
- Complete game with 6 dimensions, 15 enemies, 6 bosses
- 9 weapons, 10 skins, particle system
- Cel shading visual style
- Procedural audio
- Save/records system
