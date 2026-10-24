# Fase A, tarefa 1 — validação e decisão da release 1.8.0

Plano para aprovação, auditado em 24/10/2026. Esta branch parte de
`origin/main` em `cbe4702` e contém somente documentação. A publicação de
`v1.8.0`, novas tags e alterações em binários ficam suspensas até o checklist
Windows e uma decisão explícita do usuário. O PR de planejamento geral #34
continua separado, em rascunho e sem merge.

## Evidências verificadas

| Item | Resultado |
| --- | --- |
| Tag da candidata | `v1.8.0-rc1` aponta para `f383926f5001493273ea444c1a704012e8b06a36` |
| Commit declarado pelos dois pacotes | `BUILD-COMMIT-Windows.txt` e `BUILD-COMMIT-Linux.txt` trazem `f383926f5001493273ea444c1a704012e8b06a36` |
| Estado da candidata | Pré-release publicada com instalador, portátil, pacote Linux, arquivos de commit e SHA-256 |
| HEAD remoto auditado | `cbe4702`; há 25 commits após o commit da RC |
| Licenças na RC | `LICENSE` e `data/fonts/OFL.txt` não existem na árvore de `f383926`; o instalador e o workflow dessa revisão não incluem avisos OFL |
| Licenças na main atual | `LICENSE` e OFL existem; workflow e instalador incluem o texto OFL nos pacotes |
| Versão do instalador da RC | O workflow usa o nome da tag como `AppVersion`; portanto a compilação de `v1.8.0-rc1` identifica o instalador como `1.8.0-rc1` |
| Validação manual Windows | Ainda não realizada; o usuário informou que não consegue testar agora |

As somas publicadas na RC, conferidas com os metadados dos assets da Release,
são:

```text
INCARNATE.exe                    1643e91b6804e554a03c3932ffcb9d8f908cfac19b0d18abe541706d54ebdc09
INCARNATE-Setup.exe              f0e30d753de289f0b0b70fd90ab16c5a9dcc965ca84770e576e98f83deab9e90
INCARNATE-Linux-x86_64.tar.gz    63731e332d96f769daa861d79f6ad9f00ba283db5b20388d28dc49f9d4bbe1f4
```

Esses hashes identificam os downloads, mas não substituem teste funcional nem
garantem que a RC contenha os avisos exigidos. Não alterar nem excluir os
assets originais enquanto se decide a release.

## Decisão de design antes de executar a release

Promover **exatamente** os binários de `v1.8.0-rc1` preserva os hashes já
publicados, mas deixa duas pendências: faltam os avisos de licença junto às
fontes nos pacotes e o instalador ainda se identifica como `1.8.0-rc1`.
Além disso, esse commit não inclui os PRs #29–#33 da main. Assim, a promoção
direta não satisfaz o escopo de fechamento descrito para a Fase A.

**Proposta:** manter `v1.8.0-rc1` como registro histórico e, após aprovação,
preparar uma nova candidata a partir de um commit fixo que inclua a licença e
os avisos OFL. Definir antes do build como apresentar `1.8.0` no instalador e
como publicar os **mesmos bytes que serão testados**, sem o workflow da tag
final substituí-los por uma recompilação. Auditar o workflow nesta mesma
branch da tarefa, somente após aprovação deste design: hoje um push de tag
`v*` dispara builds e upload automático para a Release. Não criar tag de
release ou publicar binários antes dessa solução ser revisada.

Se a nova candidata partir da `origin/main` atual, levará também os PRs
#29–#33: isso amplia o conteúdo de `1.8.0` em relação à RC antiga e à projeção
do Passo 0. A alternativa de incorporar somente os avisos à base da RC também
gera novos binários e exige novo teste. A escolha da base e da versão pertence
ao usuário antes de qualquer build.

Alternativa sujeita à escolha do usuário: manter os bytes antigos apenas na
pré-release `v1.8.0-rc1`, sem declarar concluída a release final. Ela preserva
o artefato histórico e as pendências identificadas, sem representar o
fechamento proposto acima.

## Checklist Windows para o usuário, quando puder testar

1. Baixar o instalador e o portátil **da mesma candidata**; comparar cada
   SHA-256 com o `SHA256SUMS.txt` daquela candidata usando `Get-FileHash`.
   Conferir que `BUILD-COMMIT-Windows.txt` e `BUILD-COMMIT-Linux.txt` apontam
   para o commit da tag da candidata.
2. Instalar em ambiente limpo, iniciar pelo atalho e executar uma partida
   curta em ORIGINAL e COMIC. Confirmar som, mira, pausa, fechamento e gravação
   de progresso em um diretório de dados de teste.
3. Atualizar uma instalação anterior: confirmar atalho, pasta reconhecida,
   perfil e save preservados. Fazer esse teste com cópias dos dados pessoais.
4. Criar, selecionar, renomear, exportar/importar e excluir perfis de teste;
   reabrir o jogo e conferir progresso e configurações por perfil.
5. Conferir versão exibida, presença de `licenses/OFL.txt` junto às fontes e
   aviso SmartScreen/antivírus se ocorrer. Desinstalar e verificar que os dados
   do usuário não foram apagados sem pedido.

Registrar resultado, edição do Windows, nome do arquivo testado, SHA-256 e
qualquer falha reproduzível. O teste anterior do PR #34 validou apenas o plano
e o checkout da branch; não equivale a testar os executáveis da RC.

## Próxima parada

Depois da aprovação deste design, a próxima ação técnica nesta branch será
resolver o fluxo de build/promoção, com PR em rascunho e sem merge. A release
continua condicionada ao resultado manual Windows. Não iniciar a tarefa de
validação de apóstrofo nem outra fase antes de novo “pode seguir”.
