# Auditoria de integração — 18/10/2026

Referência inicial da main: `4e496edf8b1be74c5a20a59f2d2b6004fbeef361`.
O polimento do repositório (PR #26) foi integrado como `4f87f73`; a renomeação
final (PR #27) foi integrada como `f383926`. A candidata `v1.8.0-rc1` foi
gerada com builds Windows/Linux bem-sucedidos.
As branches antigas e `revert/revert-pr-13` ficam fora.

## Segurança

- `chore/polir-repo` foi publicada sem alterações em `6b32915`.
- A tag anotada `pre-integracao-2026-10-18` foi publicada sobre `4e496ed`.
- Antes do merge de renomeação, a tag `pre-rename-2026-10-18` foi publicada
  sobre a main que contém o PR #26; a tag inicial não foi movida.
- `1539f68` (`/tmp/incarnate-main-integration`) e `9d09ffc`
  (`/tmp/incarnate-stage5-baseline`) estão contidos em `main`, `origin/main`,
  `feature/polimento-visual` e `integrate/polimento-visual`.
  Não foi necessário criar tags `archive/`.
- Os worktrees registrados estavam limpos; nenhuma branch ou worktree foi removido.
  A main local permaneceu em `4e496ed`.

## Perfis: grafo de commits versus conteúdo

Comandos usados: `git cherry -v origin/main <branch>` e
`git diff <commit>^ <commit> | git patch-id --stable`.
O sinal `+` indica que o patch individual não aparece como commit equivalente
na main. Os PRs #23 e #24 foram integrados por squash; por isso o sinal não
prova que a funcionalidade esteja ausente. Commits de merge não são listados
por `git cherry`; seus patch-ids abaixo usam o primeiro pai.

| Branch | Commit | Cherry | Patch-id estável | Conteúdo e conclusão |
| --- | --- | --- | --- | --- |
| `feature/perfis-jogador` | `b535f55` | `+` | `31a6a61ee36c2cf41fe02c03428a2e454090702f` | Modelo, repositório e migração inicial. Funcionalidade presente no squash #23 (`0f374dd`). |
| `feature/perfis-jogador` | `843c08d` | `+` | `13c4e9472388e57c053b571b9087bf657471d7e8` | Seleção de perfil e integração de progresso. Funcionalidade presente no #23; arquivos de loop/configuração evoluíram depois. |
| `feature/perfis-jogador` | `0f04402` | merge | `8ac5fdff14ae80cb164f2f4a744caecdf6cea3c4` | Integra a main/shader e resolve settings. Não acrescenta uma feature de perfis exclusiva. |
| `feature/perfis-jogador` | `3c21bea` | `+` | `7da657c27bbf9c32d5940459803b44e5267ea20d` | Transferência por CLI; patch idêntico a `a41c018`. |
| `feature/perfis-jogador` | `91c72b9` | `+` | `e33ec80fb65aa31fe96778f81b4361ea2c891251` | Documentação de perfis/1.5.0; patch idêntico a `e6df062`. |
| `feature/perfis-jogador` | `ee05ae9` | merge | `8ac5fdff14ae80cb164f2f4a744caecdf6cea3c4` | Reúne as atualizações remotas; mesmo delta do merge `0f04402`. |
| `feature/perfis-jogador-finalizacao` | `a41c018` | `+` | `7da657c27bbf9c32d5940459803b44e5267ea20d` | Transferência por CLI; equivalente a `3c21bea`. |
| `feature/perfis-jogador-finalizacao` | `e6df062` | `+` | `e33ec80fb65aa31fe96778f81b4361ea2c891251` | Documentação; equivalente a `91c72b9`. |

O delta agregado `843c08d..91c72b9` e o delta
`0f374dd..e6df062` têm patch-id
`60e51fd2311a4052befc7c519c7ea5cf5307b55e`, exatamente o mesmo do squash
`77a3550` (#24) na main.

O delta agregado dos dois commits iniciais tem patch-id
`c30708ecb61ba6900d9ce783e58f1ee3f14a9c11`; o squash #23 tem
`1be32667281610a8c6b980e5bbdba2efb94f92fb`. Aqui a equivalência é funcional,
não um patch idêntico: as bases diferem pela integração do shader/settings.
Modelo, repositório, serviço, tela e testes de perfis têm conteúdo igual ao da
main auditada. Dos 25 arquivos do #23, 17 têm blobs idênticos às branches;
os oito restantes receberam mudanças posteriores em settings, core, loop,
progression, debug overlay, menu e seus testes.

**Exclusividade funcional confirmada nas duas branches: nenhuma.**
Integrá-las novamente recolocaria versões antigas de arquivos que a main já
evoluiu. Os commits e as branches permanecem preservados para consulta.

## Branches antigas: funcionalidades procuradas

Nenhuma funcionalidade ausente na main foi confirmada entre as frentes abaixo.
A tabela registra os candidatos e onde o conteúdo equivalente existe hoje,
para evitar reimplementar trabalho já integrado. Isso não equivale a validar
todas as variantes visuais históricas pixel a pixel.

| Branch antiga | Funcionalidade candidata | Código atual / integração | Falta na main? |
| --- | --- | --- | --- |
| `feat/melhorias-gerais` | Checkpoint de campanha e progressão | `game/phase_select.py`, `src/runtime/infrastructure/persistence/save_system.py`, `src/runtime/controllers/progression.py`; #14/#15 | Não. Retoma fase/nível; não serializa uma partida inteira em andamento. |
| `feat/melhorias-gerais`, `test/windows-exe` | TAB, bomba antes do descarte, escala GPU, recordes/arsenal | `controllers/loop.py`, `controllers/combat.py`, `infrastructure/graphics/gpu_renderer.py`, `presentation/screens/records_screen.py`, `equipment_overlay.py` sob `src/runtime/`; #14–#16 | Não. |
| `feat/distribuicao-windows` | Instalador, assinatura, perfis gráficos, monitor, confirmação de resolução e fallback em janela | `.github/workflows/windows-exe.yml`, `installer/incarnate.iss` (antes `void-shift.iss`), `src/runtime/application/core.py`, `src/runtime/presentation/menu.py`; #16/#17 | Não. |
| `feat/paridade-desktop-linux-windows` | XDG, escrita atômica, passo fixo, métricas, grade espacial, menu mais rápido | `src/shared/user_data.py`, `src/shared/persistence.py`, `src/runtime/application/timing.py`, `diagnostics/frame_metrics.py`, `domain/spatial.py`, `presentation/menu.py`; #19 | Não. |
| `feat/gameplay-polimento` | Visual comic, painéis/botões, opções de menu uniformes | `src/infrastructure/graphics/comic_*`, `src/runtime/infrastructure/graphics/smooth.py`, `src/runtime/presentation/menu.py` e `screens/`; squashs e integrações posteriores | Não. |
| `feat/minibosses-visual-instalador` | Minibosses e melhorias de distribuição | `src/runtime/domain/entities/minibosses/`, controlador e testes; #21 (`b4b7186`) | Não; `git cherry` também marca equivalência. |
| `feature/shader-comic-gpu` | Shader GLSL, composição separada e lobby comic | `src/runtime/infrastructure/graphics/gpu_renderer.py`, `game/phase_select.py` e testes OpenGL; #22 | Não. |
| `revert/revert-pr-13` | Reversão histórica | Fora da integração por decisão explícita | Não avaliar para merge. |

## Renomeação e dados

- Atualizar nomes de produto, pacote/comando principal, executáveis, atalhos,
  instalador, artefatos e documentação corrente para INCARNATE.
- Preservar o AppId Inno Setup
  `{B74AE7B0-9A9F-4C93-9A30-0D51F7C91000}` e reutilizar o diretório de uma
  instalação anterior. O instalador reconhece atualizações pelo AppId.
- Preservar `VoidShift`/`void-shift` como diretórios de dados e
  `SPACEFURY_DATA_DIR` como fallback. `INCARNATE_DATA_DIR` já tem prioridade.
- Não há benefício funcional em copiar todos os dados agora. Uma futura
  migração opcional deve copiar para um diretório novo somente quando o destino
  não existir, validar os JSON/backups e manter a origem intacta. Não mover.
- Nomes antigos em histórico, no PDF de análise e em nomes internos de imagens
  permanecem como referências históricas/compatibilidade, sem trocar os assets.

## Verificações da integração do repositório

- 601 testes passaram, 1 OpenGL foi ignorado localmente.
- Smoke CLI e 20 testes headless de fluxo passaram.
- Ruff passou nos arquivos alterados e no conjunto já coberto pelo CI;
  177 achados globais anteriores permanecem fora do escopo.
- Dois erros antigos de mypy impediam o CI: corrigidos com `typing.cast`,
  sem modificar valores ou regras de jogo.
- Perfil criado na main anterior carregou com identidade, progresso e
  preferências iguais. Migração de save legado preservou os arquivos originais.
- Benchmark em Linux, Python 3.14.8, pygame-ce 2.5.8, SDL dummy, 1280×720,
  COMIC/MEDIA, 61 entidades, 120 quadros × 5 repetições, duas rodadas:

| Medida (ms; faixa entre rodadas) | Main anterior | Integração |
| --- | --- | --- |
| Média sem avanço | 2,176–2,213 | 2,197–2,313 |
| p95 sem avanço | 3,472–3,559 | 3,566–3,638 |
| Média com avanço | 4,063–4,267 | 4,079–4,206 |
| p95 com avanço | 5,290–5,529 | 5,405–5,615 |

O benchmark agrega as repetições pela mediana das métricas de cada repetição.
As faixas com avanço se sobrepõem; o desenho do mundo não foi modificado.

## Renomeação final: validação, integração e candidata

- `chore/rename-incarnate-final` parte de `4f87f73` (#26). A versão continua
  1.8.0; o AppId Inno Setup não mudou e `UsePreviousAppDir=yes` mantém a pasta
  anterior de instalação.
- A CLI nova é `incarnate`/`python incarnate.py`; `void-shift` e `python main.py`
  permanecem como compatibilidade. Os diretórios de dados antigos continuam
  intactos e `INCARNATE_DATA_DIR` tem prioridade sobre `SPACEFURY_DATA_DIR`.
- Suíte: 602 passaram, 1 teste OpenGL foi ignorado. Ruff passou nos arquivos
  Python alterados. Os dois lançadores passaram `--smoke-test`; o benchmark de
  orçamento `tools.benchmark_runtime --check` passou.
- Benchmark de percurso em ambiente idêntico (Linux x86_64, Python 3.14.8,
  pygame-ce 2.5.8, SDL dummy, 1280×720, COMIC/MEDIA, 61 entidades,
  120 quadros × 3 repetições): média/p95 do mundo com avanço foi
  4,771/6,366 ms em `4f87f73` e 4,873/6,629 ms nesta branch. Os intervalos
  entre as três amostras se sobrepõem; a mudança foi de identidade/empacotamento.
- Memória cacheada de marcos, igual nas duas versões: 435.000 bytes (BAIXA),
  610.092 bytes (MEDIA), 753.200 bytes (ALTA).
- O PR #27 passou nos checks Linux/Windows, Ruff/mypy, OpenGL e empacotamento.
  A tag `v1.8.0-rc1` aponta para `f383926`; ambos os workflows publicaram os
  executáveis/instalador e somas SHA-256 como pré-release.
