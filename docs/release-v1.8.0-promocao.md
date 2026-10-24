# Fase A — preparar binários verificáveis para 1.8.0

Plano e procedimento de revisão. Esta branch parte da `origin/main` e não
altera gameplay, versão do pacote, hitboxes ou balanceamento. O usuário
autorizou o merge do PR de preparação; a publicação da versão final continua
dependendo do teste manual dos binários Windows.

## Problema

`v1.8.0-rc1` aponta para `f383926`. Os pacotes dessa revisão antecedem
`LICENSE` e o texto OFL no instalador/pacote Linux. Além disso, o instalador
gerado de uma tag `rc` mostra `1.8.0-rc1`. Reutilizá-lo como release final
deixaria as licenças de fontes de fora. Criar `v1.8.0` no workflow atual faria
uma nova compilação, que não seria o arquivo testado no Windows.

## Decisão técnica para esta branch

1. Gerar os artefatos de teste pela execução **push** da branch desta tarefa.
   Assim `github.sha` é o commit real da branch, e os dois arquivos
   `BUILD-COMMIT` podem ser comparados a ele. Em `pull_request`, o SHA padrão
   representa um merge temporário; não usar os artefatos desse evento para a
   promoção. A versão do instalador no push de branch vem do
   `pyproject.toml`, atualmente `1.8.0`.
2. Fazer o workflow de executáveis rodar no push desta branch. Manter a execução
   de PR para verificar integração, mas identificar o **push** como origem dos
   arquivos que o usuário testará.
3. Excluir especificamente a tag final `v1.8.0` do gatilho de build automático.
   Depois de aprovação, criar a tag no **mesmo commit** que gerou os artefatos
   aprovados e anexar os arquivos já testados à Release final por procedimento
   manual. Outras tags continuam usando o comportamento existente.
4. Se a branch mudar após o teste, invalidar o teste e entregar os artefatos
   de um novo push. A integração futura precisa preservar o SHA do commit
   testado na história da `main` (merge commit, sem squash/rebase). Criar tag de
   segurança na `origin/main` antes do merge, quando ele for aprovado.

Os filtros negativos de tags seguem a
[documentação do GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
O SHA de um evento `pull_request` é descrito na
[referência de eventos](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Como validar os binários desta branch

- Na aba **Actions → Executáveis Desktop**, escolher a execução de evento
  **push** da branch e conferir que Windows e Linux passaram. Baixar os
  artefatos `INCARNATE-Windows` e `INCARNATE-Linux-x86_64` da mesma execução.
- Comparar `BUILD-COMMIT-Windows.txt` e `BUILD-COMMIT-Linux.txt` com o SHA do
  push. Verificar `SHA256SUMS.txt` com `Get-FileHash` no Windows e
  `SHA256SUMS-Linux.txt` com `sha256sum -c` no Linux.
- Conferir `licenses/OFL.txt` no instalador e no pacote Linux, a versão
  `1.8.0` do instalador e os avisos de SmartScreen/SHA-256 do README.
- Fazer instalação limpa, atualização de instalação anterior com cópia de
  saves, partida curta, perfis e desinstalação. Registrar hash, SHA do commit,
  resultado e edição do Windows. O teste funcional ainda cabe ao usuário.

## Trava de publicação

O merge desta branch foi autorizado pelo usuário. Isso não autoriza criar
tags, publicar ou editar uma Release, nem anexar ou substituir assets públicos.
A `v1.8.0` e uma nova RC continuam bloqueadas até o usuário testar os binários
Windows manualmente. Depois do teste, conferir que os hashes dos arquivos
publicados são os mesmos dos downloads aprovados. A tag `v1.8.0` deve apontar
para o SHA declarado pelos dois pacotes e estar contida na `origin/main`
aprovada. O workflow não compilará novamente ao receber essa tag. Registrar
no ROADMAP, README, CHANGELOG e AI_USAGE o resultado real; não declarar release
concluída antes.
