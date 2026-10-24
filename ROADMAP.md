# ROADMAP — INCARNATE

Estado auditado em 18/10/2026. As regras de trabalho do agente foram consolidadas em `AGENTS.md`. PR #26 (polimento do repositório) e PR #27
(renomeação final) estão integrados na main. A candidata `v1.8.0-rc1` foi
publicada e seus builds Linux e Windows passaram. A release oficial depende do
checklist manual no Windows.

## Integrado por versão

| Versão | Entrega presente na main |
| --- | --- |
| 1.2.0 | Mira, disparo direcional, minibosses, visual comic, shader opcional, melhoria do combate e distribuição desktop. |
| 1.3.0 | Sprites direcionais e avanço/parallax com frenagem de bosses e minibosses. |
| 1.4.0 | Motor de cutscenes, introdução/capítulo 1, Arquivo de Memórias e persistência de cenas. |
| 1.5.0 | Perfis locais, CRUD, progresso individual, migração do save único e transferência por CLI (#23/#24). |
| 1.6.0 | Fundo com marcos e evolução do percurso; polimento de PREENCHE, HUD/tipografia e cutscenes. |
| 1.7.0 | Composições próprias dos fundos e contraste dos projéteis. |
| 1.8.0 | Contornos/hachuras de sprites, organização do repositório, CI incremental e renomeação final de produto/distribuição para INCARNATE. |

O `pyproject.toml` permanece em 1.8.0, conforme decisão de integração.
O CHANGELOG usa versões únicas da mais recente para a mais antiga.
As branches antigas foram preservadas. A análise de equivalência de commits
e funcionalidades está em [auditoria de integração](docs/integration-2026-10-18.md).

## Em validação

- A RC `v1.8.0-rc1` aponta para `f383926` e antecede `LICENSE` e os avisos OFL
  nos pacotes. Os artefatos do build #40125004991, commit `f020cb0`, estão
  integrados pela PR #36; checks e hashes passaram, mas o teste manual Windows
  ainda falta. RC2, tag e release final aguardam esse teste. Ver
  [procedimento de promoção](docs/release-v1.8.0-promocao.md).
- Nomes de perfil: o PR #37 integrado aceita apóstrofo, hífen, acentos e
  espaços internos, rejeitando controles e espaços nas pontas; perfis legados
  continuam legíveis e exportáveis.
- B2: etapa 1 integrada (f22ddf4, PR #31); cinco itens e hubs Jogar/Perfil
  integrados via PR #42, com teste manual de navegação pendente.
- Build candidato da PR #36: instalação limpa, atualização, jogo, perfis e
  desinstalação ainda precisam de validação manual no Windows.
- Confirmar a aparência e o comportamento dos atalhos na atualização de uma
  instalação antiga. AppId e diretórios de dados são preservados.

## Trabalho que falta

- Roteiro: revisar o próximo capítulo e implementar os capítulos 3 a 6,
  falas de minibosses e encerramento final. O JSON atual contém a introdução
  e o capítulo 1; o motor já suporta os gatilhos necessários.
- Polimento visual: etapas 2, 3 e 4 e os contornos da etapa 5 já estão na main.
  Conferir ícones e todos os estados de UI da etapa 5 em uma revisão visual
  posterior; não reimplementar HUD/fundos que já foram integrados.
- Tutorial: há dicas na tela de carregamento, mas a busca no runtime não
  identificou um fluxo completo de tutorial contextual. Conferir a divergência
  com a entrada antiga do CHANGELOG antes de implementar.
- A limpeza Ruff e a licença MIT/OFL chegaram à main pelos PRs #29 e #30; a
  OFL foi conferida no pacote Linux e está configurada no instalador Windows.

## Lista de melhorias de game design e engenharia

Referência histórica: [plano de melhorias](docs/VOID-SHIFT-plano-de-melhorias.pdf).
Estas propostas exigem tarefas e playtests próprios.

| Item do plano | Estado / próxima ação |
| --- | --- |
| Combo e dano de Íon/Gauss | Correções já documentadas na 1.2.0; continuar playtest de consistência. |
| Simulação com passo fixo | Existe em `src/runtime/application/timing.py`; preservar paridade em mudanças futuras. |
| Diretor de encontros por ameaça | Proposta pendente; não alterar ondas durante integração. |
| Upgrades e cascos com escolhas estratégicas | Catálogo básico de módulos existe; aprofundamento pendente. Não tornar melhorias permanentes. |
| Leitura visual e acessibilidade | Mira, HUD, contraste, redução de efeitos e fundos evoluíram; validar com usuários e diferentes monitores. |
| Reduzir responsabilidades de Jogo | Controladores já extraídos; continuar somente em tarefa de arquitetura. |
| Resultado comum de dano/efeitos | Auditoria e desenho ainda pendentes; preservar combate atual. |
| Proteção de saves | Escrita atômica, backups, perfis e migração já integrados; ampliar casos de falha quando necessário. |
| Testes e distribuição | CI Linux/Windows/OpenGL e builds ativos; falta a validação manual da candidata. |
| Performance | Benchmarks existentes; manter média/p95 e ambiente registrado em cada mudança relevante. |

## Dívidas técnicas conhecidas

- `game/phase_select.py` ainda tem implementação real. O restante de `game/`
  é majoritariamente fachada; não remover até cumprir os critérios do
  [mapa de arquitetura](docs/architecture-migration.md).
- `src/domain`, `src/infrastructure` e `src/presentation` mantêm módulos
  paralelos aos usados pelo runtime. Auditar consumidores antes de unificar.
- `AGENTS.md` ainda descreve comandos e detalhes da arquitetura antiga;
  atualizar esse guia em uma tarefa de documentação própria.
- O checkpoint salva campanha/fase/nível; não representa um snapshot integral
  da partida, das entidades ou dos módulos temporários.
- Íon permanece vertical, conforme limitação já documentada no README.
- Os diretórios `VoidShift`/`void-shift` e a variável `SPACEFURY_DATA_DIR`
  permanecem por compatibilidade. Não há necessidade funcional de migrar os
  dados nesta release. Se isso mudar, copiar e validar sem mover a origem.
- Os dois erros de tipagem que impediam o CI foram resolvidos na integração
  com `typing.cast`, sem mudança de regras. Outros bugs encontrados devem ser
  registrados aqui, sem correção incidental no merge.
