# Fase A — nomes de perfil

Decisão atual do usuário em 24/10/2026: **aceitar apóstrofos** em criação e
renomeação, assim como hífens, acentos e espaços internos. Rejeitar nomes vazios,
controles e espaços nas pontas; manter o limite configurado e a unicidade.
Nomes de perfis existentes não serão reescritos. A decisão anterior de manter
a rejeição foi substituída por este pedido.

## Contrato verificado

- `_name()` aceita texto Unicode imprimível, inclusive pontuação, apóstrofo,
  hífen, acentos e espaços internos. Normaliza para NFC sem remover caracteres.
  Espaço em qualquer ponta e caracteres de controle/não imprimíveis são
  rejeitados; o limite configurável continua valendo. A tela de perfis já usa
  `event.unicode.isprintable()`, portanto a validação segue a mesma entrada.
- `create()` e `rename()` aplicam a mesma validação e salvam o nome aceito
  sem aparar espaços silenciosamente.
- Um perfil antigo cujo JSON já contenha apóstrofo no nome deve poder ser
  carregado, listado, selecionado e exportado sem ter seu nome corrigido
  silenciosamente. A importação atual cria um novo perfil chamado `IMPORTADO`;
  esta tarefa não muda essa regra. A validação de novas entradas não deve
  apagar dados legados.

## Verificação e parada

Atualizar os testes de criação e renomeação por TDD, mantendo o teste de
carregamento, reconstrução do índice e exportação de nome legado. Rodar a suíte
direcionada e a completa e passar Ruff nos arquivos Python alterados. Não
reescrever saves reais nem criar migração. O PR fica em rascunho para o usuário
testar; nenhum merge é feito nesta tarefa.
