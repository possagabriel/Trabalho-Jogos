# Fase F — LINEAR e MUNDO ABERTO

**Estado:** proposta para decisão do usuário. Não iniciar código até as
decisões da seção 11 serem respondidas.

## 1. Objetivo e limites

Adicionar **MUNDO ABERTO** como modo opcional ao lado do **LINEAR**. O modo
LINEAR deve manter o fluxo, a progressão, o combate e o resultado visual atuais.
Os modos compartilham sistemas de combate e apresentação onde isso não altera
o comportamento do LINEAR.

O protótipo cobre uma região, uma toca de boss, uma estação, um perigo, uma
patrulha de miniboss e 3 a 5 destroços. A viagem rápida fica fora do protótipo.
Não adicionar dependências além das já usadas pelo jogo.

## 2. Fluxo de jogo

- **JOGAR** abre cartões para LINEAR e MUNDO ABERTO. Cada cartão resume o
  progresso daquele modo no perfil ativo; um modo sem partida mostra “Novo”.
- **CONTINUAR** retoma o último modo usado e seu ponto salvo.
- Esc retorna à tela anterior com o foco restaurado.
- Uma partida nova no LINEAR continua usando a progressão linear atual.
- Uma partida nova no MUNDO ABERTO inicia no checkpoint inicial da região do
  protótipo.

## 3. Estratégia de modos e sistemas compartilhados

Proposta: um contrato pequeno de modo com operações de iniciar, atualizar,
desenhar, receber eventos e salvar. O adaptador LINEAR chama o fluxo atual sem
reimplementar seus controladores. O MUNDO ABERTO fornece mapa, câmera,
exploração e estado de região próprios.

Compartilhar combate, armas, entidades, bosses, minibosses, áudio, cutscenes,
perfis, catálogo de Memórias e preferências. O modo escolhido controla apenas
progressão, mundo, posição, checkpoint e regras próprias. Os eventos existentes
de início e derrota/entrada de boss devem acionar as cutscenes; novos eventos
ficam limitados a interações do mundo, como coletar eco, ativar estação e cruzar
fenda.

O critério de paridade do LINEAR é comparar o fluxo anterior e o adaptador novo:
mesmas entradas, mesma sequência de fases, mesmos bosses, recompensas, saves,
cutscenes e comportamento de pausa. Nenhuma regra do LINEAR deve depender do
mapa aberto.

## 4. Mapa: dados versus geração procedural

| Opção | Benefícios | Custos e riscos |
| --- | --- | --- |
| Mapa desenhado em dados | Posição de história, bosses, estações e destroços é controlável; fácil revisar e testar requisitos de acesso | Mais trabalho manual para compor e manter as regiões |
| Mapa procedural com semente | Variação reproduzível e expansão mais barata | Pode criar rotas ruins, bloquear a leitura da história ou produzir dificuldade desigual |

**Recomendação para decisão:** autoria em dados para a topologia e os pontos de
interesse; geração por semente fixa para decoração. Cada região declara limites,
saídas, fendas, toca, estação, destroços e perigos. A semente só altera
asteroides, estrelas e pequenos detalhes sem colisão ou significado narrativo.

```json
{
  "id": "espaco_profundo",
  "dimensao": 1,
  "limites": [0, 0, 3840, 2160],
  "semente_decoracao": 4101,
  "fendas": [],
  "pontos": []
}
```

O exemplo ilustra a estrutura, não fixa tamanho, coordenadas ou IDs finais.

## 5. Regiões, câmera e exploração

O mundo completo terá seis regiões relacionadas às seis dimensões. Uma região
tem limites contínuos, entradas/saídas e decoração própria. Fendas nas
fronteiras conectam regiões. A câmera acompanha a nave com suavização; o fundo,
marcos e linhas de velocidade respondem à posição e à velocidade da nave.

As tocas de boss devem ser reconhecíveis de longe e crescer visualmente com a
aproximação. Ao entrar, a câmera conduz o jogador à arena, o avanço visual
freia e os eventos existentes acionam as cenas de entrada e derrota. Sair da
arena retoma o movimento do mundo.

O radar diferencia toca, estação, destroço descoberto e objetivo por forma e
cor. A seta aponta para o objetivo ativo. O mapa mostra a região e os chunks
visitados, mantendo a névoa nos trechos ainda não explorados. Nenhum marcador
depende apenas de cor.

O limite exterior deve funcionar como borda narrativa e conduzir o jogador de
volta sem parede invisível. A relação entre essa borda e a região chamada
**Espaço Nulo** fica pendente: o design anterior descrevia Espaço Nulo como uma
das seis regiões e uma borda exterior separada.

## 6. Conteúdo do protótipo

- Uma região inicial associada à dimensão 1.
- Uma toca visível de longe e um encontro com HEXAGONO.
- Uma estação com checkpoint; decidir se o Hangar também funciona nessa estação.
- Um campo de asteroides como perigo inicial.
- Uma patrulha de miniboss.
- Três a cinco destroços com ecos que desbloqueiam cenas no Arquivo de Memórias.
- Radar, seta de objetivo e mapa com névoa por chunk.

As outras cinco regiões, fendas entre todas as dimensões, vários bosses,
perigos adicionais, estações múltiplas e viagem rápida ficam para expansão após
o playtest do protótipo.

## 7. Chunks e orçamento de desempenho

Particionar o mundo em chunks fixos relativos à câmera. Manter ativos somente
os chunks dentro de uma vizinhança 3×3; fora dela, persistir apenas estados
compactos como eco coletado, boss derrotado, estação descoberta e trecho visto.
Ativação/desativação precisa preservar posição, colisões, recompensas e estado
da patrulha ao sair e retornar.

**Orçamento inicial proposto para medir:** preservar o alvo atual de 60 quadros
por segundo; reservar até 16,7 ms por quadro no cenário de referência. O protótipo
deve reportar média e p95 e comparar LINEAR e MUNDO ABERTO no mesmo equipamento.
Limites de entidades, projéteis e partículas por qualidade serão definidos a
partir dessa medição, sem reduzir os limites do LINEAR.

Não alocar superfícies por quadro. Cachear decoração e camadas de fundo por
região/qualidade; atualizar somente entidades dos chunks ativos. Incluir um
overlay de depuração com modo, região, chunk, câmera e contagem de entidades.

## 8. Perfil e migração de saves

Proposta de separar o estado em dados compartilhados e progresso por modo:

| Compartilhado no perfil | Próprio de cada modo |
| --- | --- |
| Skins desbloqueadas/equipada, Arquivo de Memórias e estatísticas gerais | Moedas, armas, melhorias, dimensão/bosses, posição, checkpoint, tempo e estatísticas do modo |
| Preferências pessoais | No mundo aberto: ecos coletados, chunks visitados, regiões libertas e estações descobertas |

Estatísticas gerais podem ser agregadas a partir dos modos; não devem substituir
as estatísticas individuais que alimentam cada cartão de progresso. A escolha do
último modo fica no perfil.

A migração deve ser versionada e idempotente. Em perfil legado, copiar todos os
valores atuais para `modos.linear`, criar `modos.mundo_aberto` com defaults e
preservar os campos antigos durante a transição. Perfis transferidos levam o
schema novo e não perdem dados. O arquivo legado permanece intacto até uma
gravação bem-sucedida no formato novo; falhas de escrita mantêm o progresso em
memória e exibem aviso.

Forma de schema proposta, sujeita a revisão:

```json
{
  "schema_version": 2,
  "modo_ultimo": "linear",
  "compartilhado": {
    "skins": [],
    "memorias": [],
    "estatisticas_gerais": {}
  },
  "modos": {
    "linear": {},
    "mundo_aberto": {
      "regiao": "espaco_profundo",
      "posicao": [0, 0],
      "checkpoint": "inicio",
      "ecos": [],
      "chunks_visitados": []
    }
  }
}
```

O schema final deve ser decidido antes de código de persistência.

## 9. História e progressão

Requisitos de boss e ecos são dados do mapa, não condicionais espalhadas pelo
loop. Os bosses 2–4 podem ser enfrentados em qualquer ordem, com dificuldade e
recompensas equivalentes ou escaladas pelo número de bosses derrotados. Tocas
bloqueadas indicam visualmente o requisito faltante. Os eventos de boss
existentes mantêm as cutscenes atuais; destroços acionam cenas curtas uma vez e
desbloqueiam a memória correspondente.

As revelações de história dependem de flags explícitas de progressão. O mundo
não antecipa informação de capítulos ainda não concluídos. Viagem rápida não
ignora uma toca, fenda ou cena obrigatória.

## 10. Etapas e paradas

1. **F1 — Modos:** escolha LINEAR/MUNDO ABERTO, cartões de progresso,
   `CONTINUAR` pelo último modo e adaptador Strategy. Paridade do LINEAR.
2. **F2 — Câmera e fundo:** mundo vazio, movimento livre, câmera, fundo e
   parallax por posição, limites e borda narrativa. **Parada obrigatória:** GIFs
   reais da câmera e do fundo para revisão do usuário.
3. **F3 — Região:** chunks, estação/checkpoint, perigo, patrulha, radar, seta e
   mapa com névoa; orçamento de desempenho medido.
4. **F4 — Toca:** aproximação visível, entrada/frenagem de arena e cutscenes
   existentes do HEXAGONO.
5. **F5 — Ecos e saves:** destroços, Memórias, progressão persistida por modo,
   migração versionada e transferência de perfil.

Cada etapa tem testes de lógica pura, regressão de paridade do LINEAR e critérios
de aceite próprios. Não expandir além do protótipo até revisão das capturas e
resultados do playtest.

## 11. Decisões aguardando o usuário

1. Confirmar o mapa híbrido: regiões e pontos de interesse em dados, decoração
   procedural com semente fixa.
2. Confirmar os dados compartilhados e por modo da seção 8. Em particular,
   “estatísticas gerais” seriam agregadas, enquanto cada cartão também mostra
   estatísticas específicas do modo?
3. Confirmar se a região **Espaço Nulo** é uma das seis regiões, uma borda
   narrativa exterior, ou ambos com papéis separados.
4. Confirmar a posição inicial, limites e dimensões da região do protótipo e se
   a estação oferece checkpoint e Hangar.
5. Confirmar o orçamento inicial de 60 FPS/p95 16,7 ms e a medição em um
   equipamento de referência antes de fixar limites de entidades.
6. Confirmar que bosses 2–4 ficam em ordem livre e se os requisitos numéricos
   de ecos devem ser definidos já no design ou após o protótipo.
7. Confirmar se os cartões de modo mostram dimensão/bosses/tempo, ou outro
   resumo de progresso.

**Próxima ação após as decisões:** congelar o design e então planejar F1. Nenhum
código do modo MUNDO ABERTO faz parte desta proposta.
