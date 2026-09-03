# Executável Windows

O workflow **Executável Windows** gera o arquivo `VOID-SHIFT.exe` em uma máquina
Windows e o publica como artefato baixável da execução no GitHub Actions.

O executável inclui imagens, fontes e o ícone de Windows. Progresso e
configurações ficam em `%LOCALAPPDATA%\VoidShift`, fora da pasta do aplicativo.

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
