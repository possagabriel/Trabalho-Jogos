# Fase A — preparar binários verificáveis para 1.8.0

Plano e checklist da promoção. A PR #36 já está integrada; este documento não
autoriza merge, tag, RC ou release. A publicação continua dependendo do teste
manual dos binários Windows.

## Problema

`v1.8.0-rc1` aponta para `f383926`. Os pacotes dessa revisão antecedem
`LICENSE` e o texto OFL no instalador/pacote Linux. Além disso, o instalador
gerado de uma tag `rc` mostra `1.8.0-rc1`. Reutilizá-lo como release final
deixaria as licenças de fontes de fora. Criar `v1.8.0` no workflow atual faria
uma nova compilação, que não seria o arquivo testado no Windows.

## Candidato congelado para teste manual

Usar os artefatos do evento **push** do [build #40125004991](https://github.com/possagabriel/Trabalho-Jogos/actions/runs/40125004991),
gerados em `f020cb0edbcd2f60fa08d7a8805313e326026c60`. Esse commit foi integrado
na PR #36; a árvore do artefato é idêntica à `origin/main` em `0084abf`.
Os checks de Linux, Windows, Ruff, OpenGL e empacotamento passaram. O instalador
reporta versão `1.8.0` pelo `pyproject.toml`; não é uma RC publicada.

Hashes conferidos localmente:

- `INCARNATE-Setup.exe`: `b8dfa6c5081d256d72f8bc6803d7d50caf979b910ea0303f79b8ecc36551837c`
- `INCARNATE.exe`: `47afde29527d4a8b4115cb5d6c5e65f3923f6905d91079973f559fc3c16dd752`
- `INCARNATE-Linux-x86_64.tar.gz`: `cc3173585566392bf67f61deffcababbb7a158d1f03bc1bb60a5f93be24e3e99`

Não substituir esses arquivos por um novo build depois do teste. A RC1 `f383926`
é anterior à inclusão de `LICENSE` e OFL e não é candidata à promoção. RC2 e
release final ficam para depois do resultado Windows e da aprovação explícita.

Os filtros negativos de tags seguem a
[documentação do GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
O SHA de um evento `pull_request` é descrito na
[referência de eventos](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Checklist manual no Windows

- Antes de atualizar, faça backup de `%LOCALAPPDATA%\VoidShift` (por padrão,
  `C:\Users\<usuário>\AppData\Local\VoidShift`).
- Baixe `INCARNATE-Windows` do build #40125004991; confira
  `BUILD-COMMIT-Windows.txt` (`f020cb0…`) e compare os dois executáveis com
  `SHA256SUMS.txt` usando `Get-FileHash` no PowerShell.
- Instale em uma máquina limpa; abra pelo atalho e inicie uma partida curta.
- Confira que o instalador informa `1.8.0` e que a instalação contém
  `licenses\OFL.txt`.
- Atualize uma instalação anterior; confira atalhos, abertura do jogo e
  preservação dos perfis/saves do backup.
- Crie ou selecione um perfil e confirme que os dados continuam disponíveis.
- Desinstale e confirme que o jogo foi removido e os dados do usuário seguem
  preservados para recuperação.
- Anote edição/versão do Windows, hashes, resultado de cada item e qualquer
  falha. O aviso SmartScreen/antivírus é esperado em binários sem reputação;
  valide o SHA-256 antes de executar.

No Linux, `sha256sum -c SHA256SUMS-Linux.txt` passou. O tar inclui
`INCARNATE/licenses/OFL.txt`; o instalador Windows referencia
`{app}\licenses\OFL.txt` no script Inno Setup. A confirmação do arquivo após
instalação faz parte do teste manual.

## Trava de publicação

Este documento não cria nem autoriza tag, merge ou release. A `v1.8.0` e uma
nova RC continuam bloqueadas até o usuário testar os binários Windows e aprovar
os próximos passos. Depois do teste, registrar o resultado real nos docs; não
declarar release concluída antes da promoção explícita dos mesmos arquivos.
