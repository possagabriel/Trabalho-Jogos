# Minibosses do mundo aberto — encontros 2D

**Status:** proposta de design; nenhuma implementação. O modo LINEAR conserva os sete tipos, seus ataques, recompensas e frequência atuais. As regras abaixo pertencem só ao MUNDO ABERTO. Profundidade visual usa escala e sombra em camadas 2D; colisões continuam no plano 2D, sem eixo Z nem OpenGL.

**Regiões:** R1–R6 são as seis regiões por dimensão de `mundo-aberto.md`; R1 é a região inicial e R5 inclui Espaço Nulo. Afinidade aumenta peso, não restringe um tipo a uma única região. Vazio exterior não recebe spawn.

**Ajuste das ideias de partida:** MATRIZ divide só em marcos de vida para limitar drones, CARTÓGRAFO reaproveita zonas como minas, ECO preserva a cópia de tiros, e a emboscada pertence ao ESPECTRO; quatro tipos novos cobrem perseguição, gravidade, anel e roubo.

## Catálogo existente e proposta por tipo

Cada “Hoje” ocupa duas linhas e descreve o runtime atual. Nas mecânicas propostas, o ciclo de **aviso → ataque → recuperação** permanece; cada ataque perigoso recebe pelo menos **0,6 s** de telégrafo antes de causar dano. A chave da fala usa o mecanismo existente `miniboss:<tipo>` e dispara só no primeiro encontro daquele tipo no perfil do mundo aberto.

### 1. BASTIÃO // FIREWALL (`bastiao`)

Hoje: dois núcleos laterais interceptam tiros; o casco não recebe dano enquanto algum vive.
Hoje: move-se lateralmente, dispara leque e só expõe o centro após destruir os dois núcleos.

**Mecânica (3 linhas):**
1. Os dois núcleos alternam um feixe de guarda que ocupa uma faixa curta do espaço.
2. Destruir um núcleo abre um corredor permanente no feixe; o outro continua vulnerável.
3. Sem núcleos, o feixe cessa e o centro recebe dano como hoje.

**Telégrafo:** linha tracejada com ponteiros nas duas pontas e som grave por 0,8 s antes do feixe; o leque mostra cone vazado por 0,6 s.
**Derrota e ponto fraco:** acertar ambos os núcleos laterais, depois o centro; núcleo não protegido é o ponto fraco.
**Dificuldade/afinidade:** 1; R1–R2. **Recompensa:** 12 moedas do mundo aberto; revela um destroço próximo.
**Primeiro encontro:** `miniboss:bastiao` — “Dois núcleos guardam esta passagem.”

### 2. ESPECTRO // BACKDOOR (`espectro`)

Hoje: marca uma posição atrás do jogador, salta até ela e dispara um tiro mirado.
Hoje: durante o ataque permanece no destino; na recuperação volta ao topo da arena.

**Mecânica (3 linhas):**
1. Na aproximação, a silhueta some fora do raio curto; sonar revela seu contorno.
2. O salto existente continua marcado no chão, mesmo quando ele ainda está oculto.
3. Após atirar, retorna visível e fica vulnerável durante a recuperação.

**Telégrafo:** contorno pontilhado do destino, seta de entrada e som de dois pulsos por 0,8 s; o tiro mirado tem retículo que fecha por 0,6 s. Invisibilidade nunca esconde esses avisos.
**Derrota e ponto fraco:** esquivar do salto e atirar na volta; o casco exposto na recuperação é o ponto fraco.
**Dificuldade/afinidade:** 2; R2–R4. **Recompensa:** 18 moedas; revela a próxima vaga de emboscada no mapa.
**Primeiro encontro:** `miniboss:espectro` — “A entrada já estava atrás de você.”

### 3. MATRIZ // FORK (`matriz`)

Hoje: invoca lacaios `scout` até o limite de três e dispara leque.
Hoje: sem lacaios, o núcleo recebe dano dobrado; o controlador remove lacaios derrotados.

**Mecânica (3 linhas):**
1. Ao cruzar 66% ou 33% de vida, um lacaio se divide se houver vaga livre.
2. Os dois drones ocupam a vaga original e a vaga livre, dentro do limite de três; não se dividem outra vez.
3. Eliminada a escolta, o núcleo mantém a janela de dano dobrado existente.

**Telégrafo:** fissura em duas metades no casco e contagem sonora por 0,8 s antes da divisão; drones nascem com contorno grande por 0,6 s antes de atirar; leque exibe cone vazado.
**Derrota e ponto fraco:** limpar os drones e aproveitar o dano dobrado; o núcleo sem escolta é o ponto fraco.
**Dificuldade/afinidade:** 2; R2–R3. **Recompensa:** 18 moedas; primeiro abate da vaga dá 1 fragmento de eco.
**Primeiro encontro:** `miniboss:matriz` — “Uma matriz basta para muitas cópias.”

### 4. CENSOR // OVERRIDE (`censor`)

Hoje: inverte somente o vetor de movimento durante o estado de ataque.
Hoje: disparo e pausa continuam normais; usa o leque comum e volta ao normal na recuperação.

**Mecânica (3 linhas):**
1. Alterna o pulso de inversão existente com um pulso de interferência, nunca ambos juntos.
2. A interferência suspende sonar e radar por 2 s sem gastar a carga do sonar.
3. Seta de objetivo, borda da zona e avisos de perigo permanecem visíveis até o sinal voltar.

**Telégrafo:** ícone riscado de controle ou de antena, conforme o próximo pulso, com três batidas ao longo de 0,9 s; leque tem cone vazado por 0,6 s. Texto do HUD nomeia o pulso.
**Derrota e ponto fraco:** reconhecer o ícone, manter rota livre e atacar na recuperação; o intervalo sem pulso é o ponto fraco.
**Dificuldade/afinidade:** 2; R3–R4. **Recompensa:** 18 moedas; revela um destroço ainda não marcado.
**Primeiro encontro:** `miniboss:censor` — “O sinal será interrompido por instantes.”

### 5. CARTÓGRAFO // QUARENTENA (`cartografo`)

Hoje: fixa duas zonas durante o aviso, uma na posição inicial do jogador e outra sorteada.
Hoje: as zonas só causam dano no estado de ataque; o leque comum acompanha o ciclo.

**Mecânica (3 linhas):**
1. As zonas existentes viram minas de perímetro, fixas depois de colocadas.
2. Cada mina arma após o aviso e detona uma vez; não persegue a nave.
3. O espaço limpo entre as minas fica marcado como rota de fuga antes da detonação.

**Telégrafo:** disco tracejado com relógio de seis marcas e tique audível por 1 s; a explosão mostra círculo de alcance em contorno, e o leque mostra cone vazado.
**Derrota e ponto fraco:** sair dos círculos marcados e atacar durante a recuperação; o casco após detonar é o ponto fraco.
**Dificuldade/afinidade:** 1; R1–R3. **Recompensa:** 12 moedas; revela um caminho seguro até destroço próximo.
**Primeiro encontro:** `miniboss:cartografo` — “Esta área já está demarcada.”

### 6. ECO // MIRROR (`eco`)

Hoje: observa o último disparo real do jogador e copia até cinco tiros, sem ler a arma equipada.
Hoje: inverte direções com velocidade limitada; íon vira bala visível e bombas não explodem como aliadas.

**Mecânica (3 linhas):**
1. Mantém a cópia limitada do último disparo e grava um trecho curto do caminho da nave.
2. Uma sombra percorre esse trecho com atraso fixo, sem copiar dano da arma outra vez.
3. A sombra desaparece antes da recuperação, quando o casco fica livre para contra-ataque.

**Telégrafo:** forma ampliada dos tiros copiados e pegadas numeradas mostram disparo e rota por 0,8 s; cada projétil mantém silhueta própria. Leque substituto também mostra cone vazado.
**Derrota e ponto fraco:** oferecer disparo simples, sair do caminho gravado e atacar após a cópia; a recuperação é o ponto fraco.
**Dificuldade/afinidade:** 2; R2–R5. **Recompensa:** 18 moedas; primeiro abate da vaga dá 1 fragmento de eco.
**Primeiro encontro:** `miniboss:eco` — “O último disparo ficou registrado.”

### 7. CRONISTA // CLOCK (`cronista`)

Hoje: carrega, lança o anel `8dir` e só aceita dano na recuperação.
Hoje: a janela de blindagem e os tempos de aviso/ataque/recuperação são definidos no catálogo.

**Mecânica (3 linhas):**
1. Na recuperação, a blindagem abre um setor frontal anunciado por um recorte físico.
2. O setor gira apenas entre ciclos; não muda de lado enquanto a janela está aberta.
3. O anel de oito tiros existente conserva uma abertura para alcançar o lado exposto.

**Telégrafo:** relógio segmentado mostra o fim da blindagem por 1 s; recorte com seta aponta o lado vulnerável; oito marcas radiais antecedem o anel por 0,6 s.
**Derrota e ponto fraco:** atravessar a abertura do anel e acertar o setor indicado na recuperação; este é o ponto fraco.
**Dificuldade/afinidade:** 3; R4–R6. **Recompensa:** 24 moedas; primeiro abate da vaga dá 1 fragmento de skin.
**Primeiro encontro:** `miniboss:cronista` — “Há um instante exato para agir.”

## Quatro tipos novos propostos

As chaves abaixo são novas no catálogo e no registro, somente para MUNDO ABERTO. Seus valores de vida/dano serão calibrados sem mudar os sete tipos do LINEAR.

### 8. SENTINELA // ORBITAL (`sentinela`)

**Mecânica (3 linhas):**
1. Dispara anéis de projéteis com uma abertura larga e identificável.
2. A abertura gira entre salvas, nunca durante a mesma salva.
3. Depois de cada anel, o núcleo para de girar e fica exposto.

**Telégrafo:** oito marcas radiais com um setor vazio e seta de giro, mais batida seca por 0,8 s; projéteis são círculos com borda dupla.
**Derrota e ponto fraco:** atravessar o setor vazio e atirar na pausa; núcleo imóvel após a salva.
**Dificuldade/afinidade:** 1; R1–R2. **Recompensa:** 12 moedas; marca uma estação ainda não descoberta, se houver.
**Primeiro encontro:** `miniboss:sentinela` — “A órbita deixa uma passagem.”

### 9. CAÇADOR // VECTOR (`cacador`)

**Mecânica (3 linhas):**
1. Persegue a nave em velocidade moderada até fixar uma direção de investida.
2. Investe em linha reta até um ponto marcado, sem corrigir o rumo depois de sair.
3. Se passar do alvo, freia e oferece uma janela de dano pela traseira.

**Telégrafo:** corredor tracejado e seta no chão seguem a direção travada por 0,8 s; o som acelera em três passos; a investida deixa uma ponta triangular visível.
**Derrota e ponto fraco:** cruzar o corredor após a direção travar e atirar na frenagem; traseira exposta.
**Dificuldade/afinidade:** 2; R2–R4. **Recompensa:** 18 moedas; revela uma rota de patrulha no mapa.
**Primeiro encontro:** `miniboss:cacador` — “Sua direção foi prevista.”

### 10. GRAVITACIONAL // POÇO (`gravitacional`)

**Mecânica (3 linhas):**
1. Cria um campo de atração local com centro visível e raio limitado.
2. O boost facilita a saída, mas movimento normal sempre permite escapar a tempo.
3. O campo perde força antes de expor o núcleo; nunca coincide com mina ou toca.

**Telégrafo:** círculos concêntricos com setas apontando ao centro e pulso grave por 1 s; borda do campo permanece desenhada durante a atração.
**Derrota e ponto fraco:** afastar-se do centro, usar boost se disponível e atirar quando o campo cai; núcleo imóvel na recuperação.
**Dificuldade/afinidade:** 3; R4–R6. **Recompensa:** 24 moedas; primeiro abate da vaga dá 1 fragmento de eco.
**Primeiro encontro:** `miniboss:gravitacional` — “Toda rota encontra um centro.”

### 11. COLETOR // SALVAGE (`coletor`)

**Mecânica (3 linhas):**
1. Tenta recolher até cinco moedas soltas do mundo aberto, nunca do saldo salvo.
2. Após recolher ou falhar, foge por uma rota anunciada e deixa carga recuperável.
3. Derrotá-lo devolve a carga; se escapar, a carga reaparece no ponto de origem.

**Telégrafo:** garra aberta sobre as moedas e linha de fuga tracejada por 0,8 s; toque metálico anuncia a coleta; sem contato surpresa.
**Derrota e ponto fraco:** interceptar a fuga e acertar a garra aberta; garra durante a coleta é o ponto fraco.
**Dificuldade/afinidade:** 1; R1–R3. **Recompensa:** 12 moedas, carga devolvida e marca de um destroço de sucata.
**Primeiro encontro:** `miniboss:coletor` — “Recolhimento em andamento.”

## Sorteio justo, persistência e progressão

1. **Mapa em dados:** cada região declara zonas elegíveis, limite geométrico e vagas com ID estável, tipo de perfil, rota ou ponto de guarda, distância a estações/tocas e exclusões. Sorteio preenche uma vaga válida; não inventa topologia nem coloca ameaça em zona de calma, entrada, saída, checkpoint ou área de boss. R1 do protótipo usa uma única patrulha antes de ampliar a densidade.
2. **Semente:** combinar semente salva do mundo, ID da região e ordinal da visita com hash estável da biblioteca padrão; cada par região+visita gera a mesma sequência em testes. Desativar/recarregar um chunk na mesma visita restaura a entidade e não sorteia outra. Salvar ID da vaga, tipo, modificador, estado de vida e instante da derrota.
3. **Distância e visibilidade:** vaga precisa ficar a pelo menos 900 unidades da nave, 650 de uma estação e 800 de uma toca, além de fora da câmera antecipada e de sua margem de 250 unidades. Distâncias são propostas iniciais a validar com a escala real do mapa. Se nenhuma vaga satisfaz, adiar o encontro; jamais aproximá-lo artificialmente.
4. **Limites:** no máximo um miniboss vivo por chunk, três vivos nos chunks ativos 3×3, seis vivos por região e um engajado de cada vez. Vagas restantes aguardam sem criar inimigo fora de tela. Dois encontros não podem cobrir simultaneamente a única rota segura da nave.
5. **Sem repetição imediata:** a zona salva o último tipo gerado. Antes do sorteio ponderado, exclui esse tipo; se restar só ele, a vaga espera outra visita. Assim não há dois tipos iguais consecutivos na mesma zona, inclusive após recarregar save.
6. **Pesos:** candidatos começam pelo `peso` atual dos sete tipos; novos tipos recebem pesos provisórios 6 (sentinela), 5 (caçador), 3 (gravitacional), 6 (coletor). Afinidade regional dobra o peso. Definir progresso `P = bosses derrotados + mínimo(3, ecos coletados ÷ 3 arredondado para baixo)`; P até 1 libera dificuldade 1, P de 2 a 4 libera até 2, P a partir de 5 libera até 3. O teto sobe no máximo um grau por visita; entre elegíveis, o peso do grau do teto aumenta 10% por ponto de P (máximo 50%) e o dos graus inferiores fica pela metade. Região, bosses e ecos influenciam o sorteio sem salto de duas dificuldades.
7. **Perfis:** patrulha percorre rota declarada e avisa antes de engajar; guardião de destroço permanece próximo, sem cobrir o objeto; emboscada começa oculta, mas sonar e marcador de proximidade revelam o ponto e nenhum ataque sai antes do aviso. Perfil é escolhido pela vaga; o tipo sorteado precisa suportá-lo.
8. **Modificador opcional:** no máximo um entre `blindado` (mais resistência, mesma janela vulnerável), `veloz` (deslocamento, não encurta telégrafo) e `duplo` (segunda salva, não segunda entidade). Só entra com dificuldade 2 ou 3, no máximo 25% das vagas elegíveis e nunca no primeiro encontro de um tipo; sorteio e escolha ficam salvos. Nenhum modificador muda hitbox ou remove fuga.
9. **Respawn:** após derrota, a vaga fica vazia por pelo menos 10 minutos de tempo jogado e até o jogador sair da zona e iniciar outra visita à região. A vaga não respawna com a nave/câmera perto, nem durante cena, pausa ou combate. Fragmentos e revelações são pagos apenas na primeira vitória por vaga; novo encontro rende metade das moedas.

## Justiça, leitura e recompensas

- **Orçamento de dano por encontro:** um miniboss engajado, até 24 projéteis inimigos ativos e uma área perigosa ativa; padrões não combinam duas fontes que cubram todas as saídas. Sem dano de spawn. Ajustar dano/velocidade para que uma única falha de esquiva não cause mais que 25% da vida cheia de referência; três erros sucessivos devem permitir recuo. O teto vale em BAIXA, MEDIA e ALTA.
- **Fuga:** ao cruzar a borda da zona e manter distância segura por 3 s, o miniboss desiste, para ataques e retorna à vaga; a vida dele não se recompõe enquanto a visita estiver ativa. O jogador nunca precisa derrotá-lo para alcançar estação, toca ou fenda obrigatória. Miniboss não persegue para dentro de arena de boss.
- **Avisos:** todo ataque, investida, mina, pulso e mudança de alvo tem no mínimo 0,6 s de aviso por forma, contorno, seta, ritmo ou som; círculos, cones, linhas e projéteis têm silhuetas diferentes, além de cores. Desligar som não remove aviso visual. “Reduzir efeitos” corta estática, pulsos e sombras extras, mas mantém hitbox aparente, texto e telégrafos; máximo de três flashes por segundo, texto essencial com contraste de 4,5:1.
- **Boost, sonar e câmera:** nenhum encontro exige boost para escapar, embora ele ajude contra gravidade e investida. Sonar revela emboscada antes da agressão e o CENSOR não consome sua recarga; se estiver indisponível, marcador de proximidade substitui a detecção. A validação de distância usa a câmera com antecipação e seu retângulo visível, para não haver spawn à frente da nave nem ataque fora da tela.
- **Economia por modo:** moedas 12/18/24 para dificuldades 1/2/3, só no balde `mundo_aberto`; armas e upgrades continuam separados do LINEAR. Fragmentos de eco ou skin são primeira vitória por vaga, com teto de dois fragmentos de eco e um de skin por região; repetição nunca gera fragmentos. Revelações marcam destroço, estação ou rota já existente, sem criar objetivo novo nem antecipar história. Recompensa é concedida uma vez por ID de encontro, inclusive com save/reload.

## Desempenho e implementação futura

Ativar/updatear apenas minibosses dos chunks 3×3 perto da câmera; fora deles, guardar estado compacto, inclusive cooldown e carga do COLETOR. Reutilizar um pool de projéteis e impor o mesmo teto de 24 projéteis perigosos em todas as qualidades. Qualidade muda apresentação, não dano, frequência ou prêmio:

| Qualidade | Partículas/rastros decorativos por encontro | Sombra e leitura |
| --- | ---: | --- |
| BAIXA | até 12 | Uma sombra simples, contornos e marcas obrigatórios. |
| MEDIA | até 24 | Sombra e rastro curto, contornos e marcas obrigatórios. |
| ALTA | até 40 | Sombra em camadas e rastro longo, contornos e marcas obrigatórios. |

**Etapas pequenas, sem implementar agora:**

1. Dados de zona/vaga, semente estável e filtro de distância; protótipo com BASTIÃO e SENTINELA em R1, uma patrulha por visita, sem tocar no LINEAR.
2. Seleção ponderada, teto de dificuldade, não repetição, perfis e persistência de visita/respawn.
3. Adaptar os outros seis tipos existentes para suas mecânicas de mundo aberto; adicionar CAÇADOR, GRAVITACIONAL e COLETOR pelo registro existente.
4. Integrar HUD/radar/sonar/câmera, recompensas por modo, pooling, limite por qualidade e opção “reduzir efeitos”.

**Arquivos prováveis (confirmar na implementação):** `src/runtime/domain/entities/minibosses/config.py`, `registry.py`, `types.py`, `strategies.py`, `states.py` e `base.py` para catálogo e estratégias; módulo novo de sorteio/estado em `src/runtime/domain/world/`; dados de regiões e vagas no mundo aberto; controlador de chunks/sonar/radar e apresentação 2D; testes novos de regras puras em `tests/`.

**Testes de lógica pura:** semente igual → sequência igual; semente/visita diferente → sequência controladamente distinta; distâncias nave/estação/toca e câmera antecipada; nenhum tipo repetido na zona; limites por chunk/3×3/região; vaga sem candidato espera; cooldown e retorno de visita; pesos com afinidade, bosses e ecos; teto sobe no máximo um grau por visita; modificador único; recompensa única e balde correto; fuga, carga devolvida e estado restaurado após desativar chunk. Testes de integração posteriores verificam aviso ≥0,6 s, dano por encontro, legibilidade com efeitos reduzidos e paridade do LINEAR.

**Aceite do playtest:** três pessoas encontram pelo menos três tipos diferentes em até 10 minutos de exploração cada, usam fuga ao menos uma vez e conseguem explicar o telégrafo e o ponto fraco sem depender de cor; nenhum encontro é classificado como injusto por ataque sem aviso, spawn visível ou rota bloqueada. Revisar densidade, pesos e recompensas com esses relatos antes de ampliar regiões.
