# Migração para `src`

`src/` é a única fonte de implementação nova. O pacote `game/` não recebe
novas regras; enquanto houver consumidores antigos, seus módulos devem ser
fachadas sem estado que reexportam o módulo canônico de `src`.

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
| Domínio (jogador, inimigos, bosses, projéteis) | `src.domain` | pendente: integrar no fluxo executável |
| Apresentação e loop | `src.presentation`, `src.core` | pendente: conectar telas e estados ao `Application` |

Nenhum módulo legado deve ser removido enquanto sua linha não tiver testes de
paridade e consumidores migrados.
