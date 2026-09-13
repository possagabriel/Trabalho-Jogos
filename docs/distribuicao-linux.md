# Executável Linux

O workflow **Executáveis Desktop** gera `VOID-SHIFT-Linux-x86_64.tar.gz` em uma
máquina Ubuntu. O pacote inclui o executável, imagens, fontes e o fallback de
renderização por CPU. Quando OpenGL está disponível, a escala final usa a GPU.
No Linux, o jogo é distribuído como uma pasta autocontida para iniciar mais
rápido e evitar a extração temporária feita por executáveis de arquivo único.
O arquivo `BUILD-COMMIT-Linux.txt` identifica a revisão usada no build e deve
ser igual ao `BUILD-COMMIT-Windows.txt` da mesma execução.

Configurações e progresso ficam em `$XDG_DATA_HOME/void-shift` ou, quando a
variável não existe, em `~/.local/share/void-shift`.

## Gerar localmente

Use Python 3.10 ou superior:

```bash
python -m pip install -e ".[desktop]"
python tools/build_desktop.py
./dist/VOID-SHIFT/VOID-SHIFT
```

O workflow executa automaticamente um teste curto no pacote recém-criado antes
de publicá-lo. Para repetir a validação localmente, use
`./dist/VOID-SHIFT/VOID-SHIFT --smoke-test`.

O executável é gerado para o sistema em que o comando roda. Portanto, o build
Linux deve ser feito no Linux e o build Windows deve ser feito no Windows.

## Publicar uma versão

Ao publicar uma tag `v*`, o workflow anexa o pacote Linux, a identificação do
commit e `SHA256SUMS-Linux.txt` à Release correspondente. Para uma compilação
manual, execute o workflow na `main` e baixe o artefato
`VOID-SHIFT-Linux-x86_64`.
