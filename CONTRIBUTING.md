# Contributing to INCARNATE

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd incarnate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install the project and development tools
pip install -e ".[dev]"

# Run the game
python main.py
```

## Code Standards

- **Python**: 3.10+
- **Style**: PEP 8 (enforced by Ruff)
- **Type Hints**: Required on all public functions
- **Docstrings**: Google style for public APIs
- **Line Length**: 100 characters max

## Architecture

The production game currently follows a modular game-loop architecture under
`game/`. The `src/` tree is an experimental migration and is not distributed.

- `game/core.py` - Game loop and orchestration
- `game/player.py`, `enemies.py`, `bosses.py` - Entities
- `game/menu.py`, `phase_select.py`, `hud.py` - Presentation
- `game/save_system.py`, `settings.py`, `persistence.py` - Persistence

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
python -m pytest tests/ --cov=game
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
