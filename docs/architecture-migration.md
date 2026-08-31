# Migração para `src`

`src/` é a única fonte de implementação nova. O pacote `game/` não recebe
novas regras; enquanto houver consumidores antigos, seus módulos devem ser
fachadas sem estado que apontam para o módulo canônico de `src`.

## Navegação do código executável

O runtime de produção foi organizado em `src/runtime/`. Ele preserva a API
histórica por meio de fachadas em `game/`, mas é a fonte única que deve receber
correções de comportamento enquanto a migração das abstrações de domínio segue.
Para localizar uma responsabilidade rapidamente:

| Pasta | Conteúdo |
| --- | --- |
| `src/runtime/application/` | Composição e ciclo de vida do jogo (`core`) |
| `src/runtime/controllers/` | Loop, combate, pausa, progressão, game over e renderização |
| `src/runtime/domain/entities/` | Jogador, inimigos, bosses, armas e power-ups |
| `src/runtime/domain/world/` | Cenários, partículas e mensagens do mundo |
| `src/runtime/infrastructure/` | Ativos, gráficos, áudio, loja e persistência |
| `src/runtime/presentation/` | HUD, menu, componentes e telas |

Os módulos em `game/` são somente fachadas de compatibilidade. Eles mantêm
o mesmo objeto de módulo para que imports e patches antigos continuem válidos,
mas não são o local para adicionar comportamento.

## Regra de migração

1. Escolher uma responsabilidade coesa, e não uma tela ou classe isolada.
2. Completar a paridade funcional no módulo da camada correta em `src`.
3. Criar testes que exercitem a API canônica e a fachada temporária.
4. Converter `game/<modulo>.py` em uma fachada de importação, sem lógica.
5. Migrar os consumidores para `src` e só então apagar a fachada e seus testes
   de compatibilidade.

## Estado atual

| Responsabilidade | Fonte canônica | Compatibilidade | Cobertura |
| --- | --- | --- | --- |
| Constantes e estados | `src.core.constants` | `game.config` | `tests/test_src_migration.py` |
| Tema visual | `src.infrastructure.graphics.theme` | `game.theme` | `tests/test_src_migration.py` |
| Layout responsivo | `src.infrastructure.ui.layout` | `game.layout` | `tests/test_src_migration.py` |
| Configurações | `src.core.settings` | `game.settings` (alias de módulo) | `tests/test_src_migration.py` |
| Runtime executável organizado | `src.runtime` por camada | fachadas em `game` | `tests/test_runtime_module_layout.py` |
| Domínio (jogador, inimigos, bosses, projéteis) | `src.domain` | pendente: integrar no fluxo executável |
| Ponto de entrada | `src.core.application` | `main.py` | `tests/test_application_entrypoint.py` |

Nenhum módulo legado deve ser removido enquanto sua linha não tiver testes de
paridade e consumidores migrados.
