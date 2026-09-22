# Executável Windows

O workflow **Executáveis Desktop** gera o arquivo portátil `VOID-SHIFT.exe` e o
instalador `VOID-SHIFT-Setup.exe` em uma máquina Windows, publicando ambos como
artefato baixável da execução no GitHub Actions. Ele também publica
`SHA256SUMS.txt`, com as somas de verificação dos dois arquivos.

O arquivo `BUILD-COMMIT-Windows.txt` deve ser igual ao
`BUILD-COMMIT-Linux.txt` da mesma execução. Isso garante que os dois pacotes
foram produzidos a partir da mesma revisão da `main`.

O executável inclui imagens, fontes e o ícone de Windows. Progresso e
configurações ficam em `%LOCALAPPDATA%\VoidShift`, fora da pasta do aplicativo.
Antes de publicar os artefatos, o workflow inicia o executável, simula três
quadros e confirma uma gravação em diretório temporário.
A versão exibida pelo instalador vem da tag `vX.Y.Z`; em uma execução manual,
ela vem do campo `project.version` do `pyproject.toml`.

## Download público por Release

Para uma compilação de teste, baixe o artefato `VOID-SHIFT-Windows` ao final
da execução e execute `VOID-SHIFT-Setup.exe`. Para jogadores, publique uma tag
de versão, por exemplo `v1.0.0`:
o workflow cria uma GitHub Release e anexa `VOID-SHIFT.exe` diretamente nela.
O link de distribuição passa a ficar em **Releases** → versão mais recente →
`VOID-SHIFT-Setup.exe` (instalação com atalho e desinstalação) e
`VOID-SHIFT.exe` (versão portátil).

## Gerar localmente no Windows

Em um PowerShell, com Python 3.11 ou superior e o
[Inno Setup 6](https://jrsoftware.org/isinfo.php) instalados:

```powershell
py -m pip install -e ".[desktop]"
py tools/build_desktop.py
$AppVersion = py -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "/DAppVersion=$AppVersion" installer\void-shift.iss
Get-FileHash dist/VOID-SHIFT.exe, dist/VOID-SHIFT-Setup.exe -Algorithm SHA256
```

O executável é assinado antes de o instalador ser criado; assim, quando houver
certificado configurado no GitHub, a cópia instalada também carrega a
assinatura. Compare o hash exibido com `SHA256SUMS.txt` antes de distribuir um
build manual.

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
