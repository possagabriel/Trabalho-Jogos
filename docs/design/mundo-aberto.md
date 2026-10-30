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

O limite exterior é o **Vazio**: usa o efeito visual da borda narrativa, não tem
boss e empurra a nave de volta sem parede invisível. **Espaço Nulo** é a região
do boss ANEIS, fora do protótipo.

## 6. Conteúdo do protótipo

- Uma região inicial associada à dimensão 1.
- Uma toca visível de longe e um encontro com HEXAGONO.
- Uma estação com checkpoint e Hangar, reaproveitando a tela atual e usando o
  balde de progresso do modo ativo.
- Um campo de asteroides como perigo inicial.
- Uma patrulha de miniboss.
- Três a cinco destroços com ecos que desbloqueiam cenas no Arquivo de Memórias.
- Radar, seta de objetivo e mapa com névoa por chunk.

As outras cinco regiões, fendas entre todas as dimensões, vários bosses,
perigos adicionais, estações múltiplas e viagem rápida ficam para expansão após
o playtest do protótipo. O protótipo inclui apenas a borda exterior do Vazio,
sem a região Espaço Nulo ou o boss ANEIS.

## 7. Chunks e orçamento de desempenho

Particionar o mundo em chunks fixos relativos à câmera. Manter ativos somente
os chunks dentro de uma vizinhança 3×3; fora dela, persistir apenas estados
compactos como eco coletado, boss derrotado, estação descoberta e trecho visto.
Ativação/desativação precisa preservar posição, colisões, recompensas e estado
da patrulha ao sair e retornar.

**Meta:** 60 quadros por segundo. O benchmark do mundo, sem apresentação, deve
atingir p95 de até 8 ms em MEDIA e BAIXA. Os limites serão ajustáveis após a
medição na máquina do usuário. Se a meta não fechar, propor cortes antes de
seguir; não reduzir os limites do LINEAR.

Não alocar superfícies por quadro. Cachear decoração e camadas de fundo por
região/qualidade; atualizar somente entidades dos chunks ativos. Incluir um
overlay de depuração com modo, região, chunk, câmera e contagem de entidades.

## 8. Perfil e migração de saves

Proposta de separar o estado em dados compartilhados e progresso por modo:

| Compartilhado no perfil | Próprio de cada modo |
| --- | --- |
| Skins desbloqueadas/equipada, Arquivo de Memórias e estatísticas gerais | Moedas, armas, melhorias, dimensão/bosses, posição, checkpoint, tempo e estatísticas do modo |
| Preferências pessoais | No mundo aberto: ecos coletados, chunks visitados, regiões libertas e estações descobertas |

Estatísticas gerais são agregadas no perfil; cada cartão mostra o progresso do
modo correspondente. A escolha do último modo fica no perfil.

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
resultados do playtest. F1 só começa depois de A, B e C concluídas e aprovadas
pelo usuário. **Critério de sucesso do protótipo:** o jogador usa boost e sonar
sem instrução e encontra um eco em até 2 minutos.

## 11. Dependências e gates

F1 permanece bloqueada até A, B e C estarem concluídas e aprovadas pelo usuário.
Após F2, revisar os GIFs reais da câmera e do fundo. Se o benchmark de F3 exceder
o orçamento em qualquer qualidade, apresentar cortes propostos antes de avançar.

## 12. Cartões de modo

Cada cartão tem no máximo quatro linhas e uma versão compacta para 4:3. Exibe
situação, progresso do modo, bosses X/6, moedas e tempo daquele modo. O progresso
é dimensão e nível no LINEAR; no MUNDO ABERTO, regiões libertas X/6 e ecos.

## 13. Ordem dos bosses e ecos

Os bosses 2–4 podem ser enfrentados em qualquer ordem. Requisitos de ecos ficam
em arquivo de dados, com valores provisórios que serão fechados na F5.

## 14. Estação e loja

A estação do protótipo combina checkpoint e Hangar, reutilizando a tela atual e
lendo e gravando no balde do modo ativo. Se isso exigir lógica adicional na
loja, o protótipo terá apenas checkpoint.

## 15. Decisões confirmadas

1. **Mapa:** topologia definida em dados; decoração procedural com semente fixa
   por região.
2. **Perfil:** estatísticas gerais agregadas no perfil; progresso específico por
   modo nos cartões.
3. **Espaço Nulo e Vazio:** Espaço Nulo é a região do boss ANEIS. A borda exterior
   é o Vazio, com o mesmo efeito visual, sem boss, empurrando a nave de volta.
   O protótipo inclui só a borda do Vazio.
4. **Estação:** checkpoint e Hangar reaproveitando a tela atual, com leitura e
   gravação no balde do modo ativo. Se exigir lógica adicional da loja, incluir
   só checkpoint no protótipo.
5. **Desempenho:** meta de 60 FPS; benchmark do mundo sem apresentação com p95
   de até 8 ms em MEDIA e BAIXA. Ajustar após medir na máquina do usuário; se não
   atingir a meta, propor cortes antes de seguir.
6. **Progressão:** bosses 2–4 em ordem livre. Requisitos de ecos em arquivo de
   dados, provisórios até serem fechados na F5.
7. **Cartões:** situação, progresso do modo (LINEAR: dimensão e nível; MUNDO
   ABERTO: regiões libertas X/6 e ecos), bosses X/6, moedas e tempo do modo; no
   máximo quatro linhas e versão compacta em 4:3.

F1 não começa até A, B e C estarem concluídas e aprovadas pelo usuário. Este
documento registra as decisões; não inicia implementação.

## 16. Melhorias propostas

### Camada do protótipo (F2 a F5)

#### Câmera com antecipação

- Descrição: A câmera antecipa a nave na direção do movimento.<br>
  A antecipação é suavizada e configurável.
- Etapa: F2.
- Risco: movimento de câmera excessivo pode causar desconforto ou esconder ameaças.
- Como testar: comparar movimento parado, mudanças bruscas de direção e voo contínuo; conferir limite e opção de configuração.

#### Boost de exploração

- Descrição: Um boost curto aumenta a velocidade, inclina a nave e deixa rastros e linhas de velocidade.<br>
  A recarga limita o uso, e pontos do mapa dependem dele para serem alcançados.
- Etapa: F3.
- Risco: recarga ou alcance inadequados podem bloquear o avanço ou tornar o deslocamento trivial.
- Como testar: alcançar os pontos previstos, medir a recarga em jogo e validar leitura dos projéteis durante o boost.

#### Sonar de memória

- Descrição: Uma tecla dispara um pulso com recarga que revela destroços e ecos próximos.<br>
  O brilho varia com a distância e cada marcador também tem forma própria; o sonar substitui parte do radar.
- Etapa: F5.
- Risco: alcance, recarga ou brilho podem deixar ecos fáceis demais ou difíceis de localizar.
- Como testar: sem instrução, pedir ao jogador que use o pulso para encontrar um eco e verificar a leitura por forma e distância.

#### Perigo de região

- Descrição: Cada região terá um perigo com comportamento próprio.<br>
  No protótipo, o perigo é somente um campo de asteroides.
- Etapa: F3.
- Risco: densidade ou dano excessivos podem bloquear rotas e encobrir o combate.
- Como testar: atravessar o campo por rotas distintas, conferir colisões e confirmar que projéteis permanecem visíveis.

### Camada 2 (depois do playtest)

#### Zonas de calma

- Descrição: Trechos seguros alternam com as zonas de perigo.<br>
  A pausa entre encontros dá espaço para navegação e leitura do mundo.
- Etapa: Camada 2, depois do playtest.
- Risco: zonas seguras longas podem reduzir o ritmo da exploração.
- Como testar: observar pausas e encontros em percursos completos e ajustar a distância entre zonas.

#### Eventos de região

- Descrição: Regiões podem ter tempestades, caçadores ou cápsulas de memória.<br>
  Eventos aparecem no espaço e oferecem mudanças temporárias ou descobertas.
- Etapa: Camada 2, depois do playtest.
- Risco: eventos simultâneos podem sobrecarregar o HUD e competir com objetivos principais.
- Como testar: percorrer cada região com um evento ativo e verificar aviso, legibilidade e encerramento.

#### Upgrades de movimento

- Descrição: Melhorias de movimento podem abrir caminhos e pontos de exploração.<br>
  Esses caminhos funcionam como chaves de acesso no mapa.
- Etapa: Camada 2, depois do playtest.
- Risco: requisitos de movimento podem impedir retorno ou criar bloqueios sem indicação.
- Como testar: tentar cada rota antes e depois do upgrade e conferir sinalização e retorno à rota principal.

#### Região libertada

- Descrição: Libertar uma região muda suas cores, seu fundo e a fala da Voz do Protocolo.<br>
  A mudança comunica o resultado sem alterar os critérios de acesso confirmados.
- Etapa: Camada 2, depois do playtest.
- Risco: mudança visual pouco clara pode não comunicar a libertação ou reduzir contraste.
- Como testar: comparar a mesma região antes e depois da libertação, em COMIC e ORIGINAL, com efeitos reduzidos.

#### Ecos como mini-histórias

- Descrição: Cada eco pode contar uma mini-história de duas a três falas.<br>
  Os registros ampliam contexto sem antecipar revelações fora de ordem.
- Etapa: Camada 2, depois do playtest.
- Risco: falas longas ou revelações antecipadas podem interromper a exploração e confundir a sequência narrativa.
- Como testar: conferir duração de leitura, ordem de revelações e compreensão após coletar ecos opcionais.

#### Trecho de aproximação às tocas

- Descrição: Cada toca pode ter um trecho curto antes do encontro com o boss.<br>
  A aproximação prepara a arena sem alongar a entrada.
- Etapa: Camada 2, depois do playtest.
- Risco: repetição ou duração excessiva pode atrasar a luta.
- Como testar: entrar e sair da toca, medir a duração e verificar que a luta começa corretamente após a aproximação.

#### Marcadores do jogador no mapa

- Descrição: O jogador pode criar marcadores próprios no mapa.<br>
  Os marcadores registram rotas, pontos de interesse e locais para revisitar.
- Etapa: Camada 2, depois do playtest.
- Risco: excesso de marcadores pode poluir o mapa ou dificultar a leitura dos objetivos.
- Como testar: criar, mover e remover marcadores em regiões visitadas e não visitadas; conferir persistência e legibilidade.

#### Morte e retorno à estação

- Descrição: Ao morrer, o jogador retorna à última estação ativada.<br>
  A volta pode aplicar uma pequena perda, comunicada antes de confirmar a escolha.
- Etapa: Camada 2, depois do playtest.
- Risco: perda ambígua ou desproporcional pode punir exploração e desestimular o retorno.
- Como testar: morrer após ativar uma estação, conferir ponto de retorno, perda aplicada e mensagem apresentada.

### Princípios de implementação

- Densidade acima de tamanho: deve haver algo para ver ou fazer a cada 20 a 30 segundos.
- Todo efeito respeita a opção “reduzir efeitos” e o limite máximo de 3 flashes por segundo.
- Rastros e brilhos nunca escondem projéteis.
- Nenhum personagem nomeia um Protocolo Restrito em fala.
- O modo LINEAR não muda.
