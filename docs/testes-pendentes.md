# Testes pendentes por branch

Estado em 24/10/2026. Os comandos abaixo são para **PowerShell**, executados
na pasta do clone já existente. `git fetch` só atualiza referências remotas;
`git worktree add --detach` cria outra pasta e não troca sua `main` local nem
suas alterações não commitadas. Use um caminho novo para cada worktree. Nenhum
PR desta lista pode ser integrado antes da revisão e dos testes do usuário.

## `docs/roadmap-fases` — [PR #34](https://github.com/possagabriel/Trabalho-Jogos/pull/34)

Plano geral A–G, texto de referência do capítulo 2 e este arquivo. PR
documental; branch preservada mesmo se o PR estiver fechado para respeitar o
limite de PRs abertos.

```powershell
git fetch origin
git worktree add --detach ..\INCARNATE-pr34 origin/docs/roadmap-fases
Set-Location ..\INCARNATE-pr34
$env:INCARNATE_DATA_DIR = Join-Path $env:TEMP 'incarnate-pr34-dados'
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe incarnate.py
```

- **Olhar:** `docs/roadmap-fases.md`, `docs/roteiro-capitulo-2.md` e este índice.
- **Esperado:** ordem, dependências e roteiro refletem as decisões do usuário;
  o jogo abre sem alteração de gameplay. O usuário já testou a revisão inicial
  do PR; a atualização deste arquivo ainda precisa ser conferida.
- **Dependência:** nenhuma para leitura; o roteiro do capítulo 2 é referência
  para a branch de integração narrativa.

## `docs/fase-a-validacao-rc1` — [PR #35](https://github.com/possagabriel/Trabalho-Jogos/pull/35)

Auditoria da RC antiga. PR documental fechado para liberar uma vaga; branch e
worktree preservados.

```powershell
git fetch origin
git worktree add --detach ..\INCARNATE-pr35 origin/docs/fase-a-validacao-rc1
Set-Location ..\INCARNATE-pr35
$env:INCARNATE_DATA_DIR = Join-Path $env:TEMP 'incarnate-pr35-dados'
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe incarnate.py
```

- **Olhar:** `docs/fase-a-validacao-rc1.md`, sobretudo o commit dos builds, as
  licenças ausentes na RC e o checklist Windows.
- **Esperado:** o plano explica por que a RC antiga não deve virar release final
  sem novo teste. O jogo de código-fonte abre normalmente.
- **Dependência:** ler antes de testar os binários do PR #36; sem dependência
  de código ou branch empilhada.

## `ci/fase-a-promocao-binarios` — [PR #36](https://github.com/possagabriel/Trabalho-Jogos/pull/36)

Builds Windows/Linux da revisão `a60ea83f684d63b9d7b826378ab10e5220bf9a50`.
Use os artefatos da execução **push**
[Executáveis Desktop](https://github.com/possagabriel/Trabalho-Jogos/actions/runs/40061058931),
pois ela registra o SHA real da branch. O PR continua em rascunho.

```powershell
git fetch origin
git worktree add --detach ..\INCARNATE-pr36 origin/ci/fase-a-promocao-binarios
Set-Location ..\INCARNATE-pr36
$env:INCARNATE_DATA_DIR = Join-Path $env:TEMP 'incarnate-pr36-dados'
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe incarnate.py
```

- **Antes de atualizar:** o diretório padrão de progresso no Windows é
  **`%LOCALAPPDATA%\VoidShift`**, normalmente
  `C:\Users\<seu-usuário>\AppData\Local\VoidShift`. Faça uma cópia dessa pasta
  com o jogo fechado. `INCARNATE_DATA_DIR` (ou o fallback legado
  `SPACEFURY_DATA_DIR`) substitui esse caminho quando definido; verifique essas
  variáveis antes de escolher a pasta a copiar. Para abrir o caminho padrão:

  ```powershell
  explorer.exe (Join-Path $env:LOCALAPPDATA 'VoidShift')
  $origem = Join-Path $env:LOCALAPPDATA 'VoidShift'
  $copia = Join-Path $env:USERPROFILE ("Desktop\VoidShift-backup-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
  Copy-Item -LiteralPath $origem -Destination $copia -Recurse
  ```

- **Binários:** no diretório extraído do artefato `INCARNATE-Windows`, confira
  commit e hashes antes de executar:

  ```powershell
  Get-Content .\BUILD-COMMIT-Windows.txt
  Get-FileHash .\INCARNATE.exe, .\INCARNATE-Setup.exe -Algorithm SHA256
  ```

  Esperado: commit `a60ea83f684d63b9d7b826378ab10e5220bf9a50`;
  `INCARNATE.exe` =
  `bcf8bf74bc0bfcd9b7e32d46a13db349c3f8f3223b67e0d04d8cddf57fc0f31b`;
  `INCARNATE-Setup.exe` =
  `fa23d83fd50249697e01ad4507e89c00632bf37c381b235053228c5834fb954d`.
- **Checklist Windows:** instalação limpa; iniciar pelo atalho e pelo portátil;
  partida curta em ORIGINAL e COMIC; som, mira, pausa e gravação; atualizar uma
  instalação antiga e conferir atalho, perfis e save preservados; conferir
  versão `1.8.0`, `licenses\OFL.txt` junto ao jogo, aviso SmartScreen/antivírus
  se ocorrer; desinstalar e conferir que os dados pessoais não foram removidos.
- **Esperado:** todos os passos acima passam e os hashes correspondem. Relate
  falhas e o hash do arquivo testado. A nova RC e a release final seguem
  proibidas até esse resultado e autorização explícita.
- **Dependência:** leia #35 antes; não depende de outra branch no código.

## `test/fase-a-nomes-perfil` — [PR #37](https://github.com/possagabriel/Trabalho-Jogos/pull/37)

Validação de nomes de perfil. A decisão mais recente aceita apóstrofo, hífen,
acentos e espaços internos; rejeita espaços nas pontas e caracteres de
controle. O teste de nome legado continua no PR.

```powershell
git fetch origin
git worktree add --detach ..\INCARNATE-pr37 origin/test/fase-a-nomes-perfil
Set-Location ..\INCARNATE-pr37
$env:INCARNATE_DATA_DIR = Join-Path $env:TEMP 'incarnate-pr37-dados'
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest tests/test_profiles.py tests/test_profiles_integration.py -q
.\.venv\Scripts\python.exe incarnate.py
```

- **Olhar:** criar `O'Brien`, renomear para `D'Ávila-Sul` e criar nome com
  espaços internos. Tentar espaço no início/fim; o nome anterior deve continuar.
- **Esperado:** os nomes válidos são salvos e reaparecem após reiniciar; nomes
  com espaço nas pontas são recusados sem reescrever o perfil. O teste
  automatizado cobre reconstrução do índice e exportação de um nome legado.
- **Dependência:** independente de #36 e das branches de roteiro.

## Ordem sugerida

Revisar #34 e #35, depois testar #36 no Windows quando possível. #37 pode ser
testado em paralelo, com seu próprio `INCARNATE_DATA_DIR`. Os PRs documentais
futuros e a integração dos capítulos serão registrados aqui antes da entrega.
