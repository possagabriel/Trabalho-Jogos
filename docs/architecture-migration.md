# Migração da arquitetura legada

A aplicação em execução é composta por `main.py`, `src/core` e `src/runtime`.
Use imports absolutos para os módulos canônicos. O pacote `game/` é a camada
pública de compatibilidade: não adicione regras ou telas novas ali. A migração
continua incompleta e há uma exceção ativa indicada abaixo.

## Organização atual

| Área | Implementação usada pelo jogo | Módulos paralelos em evolução |
| --- | --- | --- |
| Aplicação e fluxo | `src/runtime/application`, `src/runtime/controllers`, `src/core` | `src/core/state_machine.py` oferece a arquitetura de estados ainda não usada no loop legado/runtime. |
| Domínio | `src/runtime/domain/entities`, `src/runtime/domain/world`, `src/runtime/domain/systems` | `src/domain/entities`, `src/domain/ai` e `src/domain/systems` mantêm uma hierarquia alternativa `Entity`/`Player`/`Enemy`; ela não substituiu as entidades do jogo em execução. `src/domain/profiles.py` e `src/domain/systems/profile_service.py` são usados pelo runtime e permanecem canônicos para perfis. |
| Infraestrutura | `src/runtime/infrastructure` para ativos, áudio, gráficos e persistência do runtime; `src/infrastructure/graphics` e `src/infrastructure/ui/layout.py` para componentes compartilhados | `src/infrastructure/input`, `src/infrastructure/persistence/save_manager.py` e adaptadores duplicados de gráficos ainda precisam de auditoria de consumidores e paridade antes de integração ou remoção. `src/shared/user_data.py` centraliza o diretório de dados. |
| Apresentação | `src/runtime/presentation` (menu, HUD e telas executadas) | `src/presentation` contém telas e componentes da arquitetura nova, ainda sem integração geral no fluxo ativo. Reutilizar esses componentes somente após validar layout e interação no runtime. |
| Compatibilidade | `game/` mantém nomes de import antigos apontando para `src/runtime` | `game/phase_select.py` ainda contém uma tela real e é importado por `src/runtime/presentation/menu.py`; deve migrar antes de `game/` poder ser tratado apenas como fachada. |

## Próximas migrações

1. Migrar `game/phase_select.py` para `src/runtime/presentation/screens/` ou
   `src/runtime/presentation/`, ajustar o import do menu e manter testes de
   navegação e loja do Lobby.
2. Para cada sistema de `src/domain`, comparar API e comportamento com as
   entidades/sistemas que o runtime usa. Integrar por responsabilidade e
   preservar regras, colisões e formato dos saves; remover implementações
   paralelas só quando não houver chamadas ativas nem consumidores externos.
3. Auditar `src/infrastructure`: layout, tema, renderer, shader comic e
   persistência de perfis já têm consumidores; controles, `SaveManager` e
   componentes gráficos antigos precisam de paridade ou de uma decisão explícita
   de descontinuação. Usar `src/shared/user_data.diretorio_dados()` para caminhos
   graváveis em todo adaptador de dados.
4. Auditar `src/presentation` contra `src/runtime/presentation`. Integrar as
   telas reutilizáveis quando reduzirem duplicação sem mudar a interação do jogo;
   remover scaffolds não usados apenas depois de confirmar que nenhum entry point
   os importa.
5. Migrar os imports internos de `game.*` para `src.*`. Manter as fachadas
   necessárias para imports públicos antigos durante um período de compatibilidade.

## Quando `game/` pode ser removido

A pasta inteira só pode sair quando todos estes pontos forem verdadeiros:

- nenhum módulo em `src/`, `main.py`, `tools/`, workflows ou empacotamento importa
  `game.*`;
- `game/phase_select.py` foi migrado e não há módulo com lógica própria no pacote;
- testes exercitam a API canônica em `src/`, e a suíte não depende de patches ou
  aliases do pacote de compatibilidade;
- os pontos de entrada e a distribuição são validados sem adicionar `game/` ao
  bundle;
- a janela de compatibilidade para consumidores antigos foi encerrada e isso
  está documentado.

Remover uma fachada isoladamente requer os mesmos checks de referências, testes,
entry points e configuração do PyInstaller. Até lá, fachadas devem continuar
finas, sem estado independente e sem lógica de gameplay.
