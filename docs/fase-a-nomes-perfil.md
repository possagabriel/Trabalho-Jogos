# Fase A — nomes de perfil

Decisão do usuário em 24/10/2026: **manter a rejeição de apóstrofos** para
criação e renomeação. Não alterar nomes de perfis existentes. Esta tarefa não
muda as regras do `ProfileService` nem a interface do jogo.

## Contrato verificado

- `_name()` aceita letras e números Unicode, espaços, `_` e `-`, após remover
  espaços das pontas e normalizar para NFC. O limite configurável continua
  valendo; apóstrofos não fazem parte dos caracteres permitidos.
- `create()` e `rename()` aplicam a mesma validação. Uma tentativa de renomear
  com apóstrofo deve falhar antes de escrever no repositório ou no índice.
- Um perfil antigo cujo JSON já contenha apóstrofo no nome deve poder ser
  carregado, listado, selecionado e exportado sem ter seu nome corrigido
  silenciosamente. A importação atual cria um novo perfil chamado `IMPORTADO`;
  esta tarefa não muda essa regra. A validação de novas entradas não deve
  apagar dados legados.

## Verificação e parada

Os testes existentes já cobrem criação e renomeação inválidas. Acrescentar um
teste focado no carregamento e exportação de nome legado com apóstrofo,
executar a suíte
direcionada e a completa e passar Ruff nos arquivos Python alterados. Não
reescrever saves reais nem criar migração. O PR fica em rascunho para o usuário
testar; nenhum merge é feito nesta tarefa.
