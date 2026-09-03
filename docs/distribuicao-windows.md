# Executável Windows

O workflow **Executável Windows** gera o arquivo portátil `VOID-SHIFT.exe` e o
instalador `VOID-SHIFT-Setup.exe` em uma máquina Windows, publicando ambos como
artefato baixável da execução no GitHub Actions.

O executável inclui imagens, fontes e o ícone de Windows. Progresso e
configurações ficam em `%LOCALAPPDATA%\VoidShift`, fora da pasta do aplicativo.

## Download público por Release

Para uma compilação de teste, baixe o artefato `VOID-SHIFT-Windows` ao final
da execução e execute `VOID-SHIFT-Setup.exe`. Para jogadores, publique uma tag
de versão, por exemplo `v1.0.0`:
o workflow cria uma GitHub Release e anexa `VOID-SHIFT.exe` diretamente nela.
O link de distribuição passa a ficar em **Releases** → versão mais recente →
`VOID-SHIFT-Setup.exe` (instalação com atalho e desinstalação) e
`VOID-SHIFT.exe` (versão portátil).

## Assinatura e aviso do SmartScreen

O aviso de arquivo potencialmente perigoso não pode ser removido por código.
Ele é decidido pelo Microsoft SmartScreen a partir da assinatura digital e da
reputação do arquivo.

Para assinar os builds, configure estes segredos no repositório:

- `WINDOWS_CERTIFICATE_BASE64`: conteúdo do certificado de assinatura `.pfx`,
  convertido para Base64;
- `WINDOWS_CERTIFICATE_PASSWORD`: senha desse certificado.

O certificado deve ser emitido por uma autoridade confiável. Mesmo assinado,
um certificado novo pode receber aviso até adquirir reputação. Não distribua
nem versione o arquivo `.pfx` no repositório.
