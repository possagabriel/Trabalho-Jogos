# Contributing to VOID//SHIFT

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd space_fury

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Code Standards

- **Python**: 3.10+
- **Style**: PEP 8 (enforced by flake8)
- **Type Hints**: Required on all public functions
- **Docstrings**: Google style for public APIs
- **Line Length**: 100 characters max

## Architecture

The project follows a hexagonal architecture:

- `src/core/` - Game engine, state machine, event bus
- `src/domain/` - Business logic, entities, systems, AI
- `src/infrastructure/` - Technical concerns (graphics, audio, persistence)
- `src/presentation/` - UI screens, components, HUD
- `src/shared/` - Cross-cutting utilities, types, interfaces

## Design Patterns

- **Singleton**: Global state (StateManager, EventBus)
- **Factory**: Entity creation (EnemyFactory, BossFactory, ProjectileFactory)
- **Observer**: Event system (EventBus with GameEventType)
- **State**: Game states (MenuState, PlayingState, PausedState, etc.)
- **Command**: Input handling (MoveUpCommand, ShootCommand, etc.)
- **Strategy**: AI behaviors (StraightAI, ZigZagAI, ChaseAI, etc.)
- **Template Method**: Entity base classes with hooks
- **Repository**: Data persistence (JsonRepository, MemoryRepository)

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src
```

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance
