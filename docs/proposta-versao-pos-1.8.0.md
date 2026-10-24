# Proposta SemVer após a 1.8.0

Proposta para revisão. Não altera `pyproject.toml`, telas, saves, tags nem
Releases. Elaborada em 24/10/2026 com `origin/main` em `cbe4702` e PRs
#34–#37 ainda sem merge.

## Critério

A [especificação SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) reserva
PATCH para correções compatíveis e MINOR para funcionalidade nova compatível.
Uma pré-release como `v1.8.0-rc1` antecede a versão final `v1.8.0`;
`1.8.1` só é um sucessor da **release final**, não da candidata.

## Dois caminhos possíveis para fechar a 1.8.0

| Base final aprovada | Conteúdo depois de 1.8.0 | Próximo número recomendado |
| --- | --- | --- |
| Binários/commit da RC antiga `f383926` | A `main` posterior trouxe cinco destinos do menu, hubs, cartão de perfil, selos e migração de dados, além de correções. | **1.9.0** para a primeira release que incluir essas funcionalidades. `1.8.1` seria estreito demais. |
| Binários novos da `origin/main` atual, como os do PR #36, após teste Windows | Essas funcionalidades já estarão na 1.8.0 final; não numerá-las outra vez. | **1.8.1** se a próxima entrega tiver apenas correções compatíveis; **1.9.0** se incluir capítulo 2, aceitação de apóstrofo ou outra funcionalidade de usuário após o corte. |

**Proposta principal:** após uma 1.8.0 final aprovada, usar **1.9.0** para o
próximo marco com funcionalidades novas. O PR #37 (nomes com apóstrofo) e a
integração do capítulo 2 contam como funcionalidades se ficarem fora do corte
da 1.8.0. Se esses PRs forem incorporados antes da versão final e testados
junto com ela, decidir o número do marco seguinte pelo conteúdo que realmente
ficar para depois. Nenhum número deve ser reservado só pelo nome da fase.

`1.8.1` permanece disponível para um pacote de correções compatíveis lançado
**após** a 1.8.0, sem nova navegação, roteiro ou regra de nomes. Uma mudança
incompatível de save/API exigiria outra avaliação; as tarefas atuais pretendem
preservar leitura dos dados anteriores.

## Evidências e pendências

- `v1.8.0-rc1` é pré-release; a 1.8.0 final ainda depende do teste Windows.
- `pyproject.toml` já declara `1.8.0`; esta proposta não o altera.
- O changelog em `Unreleased` registra a estrutura nova do menu e os campos de
  perfil. O corte exato da release será definido somente após os PRs aprovados
  e o teste dos binários correspondentes.
- PRs #34–#37 continuam separados. A proposta não exige que uma branch seja
  criada em cima de outra e não autoriza merge, tag ou Release.
