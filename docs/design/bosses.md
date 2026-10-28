# Bosses: mecânicas de arena em 2.5D

**Status:** proposta de design; nenhuma mecânica implementada.

## Contrato da luta

- O modo **LINEAR (clássico)** conserva movimentos, ataques, hitboxes e progressão atuais. Proposta de opção booleana `bosses_2_5d_mundo_aberto`: desligada durante o protótipo; depois do aceite, ligada por padrão apenas no mundo aberto, com possibilidade de desligá-la. Desligada, a arena usa os bosses clássicos.
- No mundo aberto, a entrada na arena reaproveita a frenagem do cenário e as cenas existentes; a câmera se fixa antes do primeiro ataque e se solta após a saída. `BOSS_SPAWNED` e `BOSS_DEFEATED` continuam sendo os únicos marcos de início e derrota, emitidos uma vez por encontro. A escolha livre entre as regiões 2–4 não pressupõe ordem de bosses.
- Profundidade é uma ilusão desenhada em 2D: escala, sombra deslocada e ordenação de planos. Nenhum ataque usa eixo Z, hitbox tridimensional, OpenGL ou renderização 3D. O jogador deve sempre reconhecer posição, área perigosa e rota segura no plano de colisão 2D.
- Cortes de vida seguem a estrutura atual: **fase 1:** acima de 66%; **fase 2:** de 66% até acima de 33%; **fase 3:** 33% ou menos. A fase troca uma vez ao cruzar cada corte. Ataques em andamento terminam ou são cancelados com aviso; nunca mudam de regra no meio do disparo.
- Todo ataque novo tem preparação legível por contorno, forma, posição ou ritmo sonoro, com tempo mínimo a calibrar em teste. Reduzir efeitos remove estática, distorção e pulsos decorativos, mas preserva contornos, ícones e avisos sonoros. Limite global: no máximo três flashes por segundo; texto essencial mantém contraste de 4,5:1, e projéteis nunca ficam ocultos pelo cenário ou HUD.
- As falas usam o léxico próprio de cada boss. Nenhum personagem nomeia um Protocolo Restrito; o termo só pode aparecer onde o roteiro já permite, como título de capítulo ou texto corrompido por glitch.

**Ajuste das ideias iniciais:** cada pressão de arena tem uma saída observável e duração limitada, para não produzir mortes inevitáveis com a câmera travada.

## 1. HEXAGONO — rota e retorno

**Vocabulário:** rota, retorno. Exemplo de fala: “Rota definida. Retorno pendente.”

**Mecânica nova (3 linhas):**
1. Faixas de bloqueio desenham corredores no chão; uma faixa marcada como rota permanece transitável.
2. O corredor muda após uma preparação com seta e batida curta, sem fechar a posição atual do jogador de imediato.
3. No retorno, a rota percorrida reaparece como sombra atrasada; o núcleo fica exposto ao fim do trajeto.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Um corredor largo; `leque` parte do boss e deixa a rota livre. |
| 2: ≤66% e >33% | Dois trajetos alternados; `8dir` ocupa cruzamentos, nunca todas as saídas. |
| 3: ≤33% | Rota e sombra de retorno se alternam; apenas uma inversão por ciclo. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Corredor forçado | Bordas tracejadas grossas, seta no piso e batida antes do bloqueio. |
| Retorno | Pegadas/sombra repetem o trajeto anterior com atraso visível e som de dois tempos. |
| `leque` | Silhueta aberta em forma de cone na origem antes dos projéteis. |
| `8dir` | Oito marcas radiais no piso aparecem antes do disparo. |

**Como vencer:** seguir a rota marcada, atravessar o cruzamento no intervalo e acertar o núcleo durante a pausa após o retorno.

**Riscos de balanceamento:** corredor estreito demais para a nave ou para `8dir`; mudança de faixa perto do jogador; sombra que cobre a única saída. Preservar hitbox atual e ajustar largura, demora e densidade apenas depois de validar a fuga.

**Teste de aceite:** em cada fase e posição inicial válida, há ao menos uma trajetória segura para sair do corredor antes do fechamento; matar o boss em qualquer corte encerra o bloqueio, dispara `BOSS_DEFEATED` uma vez e libera a câmera.

## 2. LOSANGO — tarefa e escopo

**Vocabulário:** tarefa, escopo. Exemplo: “Tarefa delimitada. Escopo em revisão.”

**Mecânica nova (3 linhas):**
1. Um perímetro de escopo delimita a área ativa sem causar dano por simples contato.
2. Nós numerados surgem em ordem; atingir o nó pedido abre uma janela de dano no núcleo.
3. Ao mudar de fase, o perímetro se reposiciona após aviso e a sequência de nós recomeça, sem guardar progresso impossível.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Um nó por tarefa; `8dir` sai do centro após o nó aparecer. |
| 2: ≤66% e >33% | Dois nós em ordem; `espiral` deixa um corredor para alcançar o próximo. |
| 3: ≤33% | Três nós, apresentados um por vez; o perímetro encolhe só entre tarefas. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Perímetro móvel | Linha pontilhada na posição futura, seta para dentro e aviso sonoro antes de mover. |
| Nó de tarefa | Número grande e forma vazada sobre o nó ativo; toque sonoro conta a etapa. |
| `8dir` | Oito marcas radiais surgem no centro antes do disparo. |
| `espiral` | Arco segmentado mostra sentido e primeira abertura antes dos projéteis. |

**Como vencer:** acertar os nós na ordem indicada e atacar o núcleo durante a janela de exposição; nós errados não punem com dano nem reiniciam toda a luta.

**Riscos de balanceamento:** tarefas longas demais, nó escondido sob HUD ou fora da câmera, espiral fechando o acesso. Limitar a três nós, manter alvos no plano visível e garantir tempo para atravessar o perímetro.

**Teste de aceite:** para qualquer ordem de visita ao boss no mundo aberto, a sequência é determinística e alcançável; acertar um nó errado não trava a fase, e todos os nós aparecem dentro da arena.

## 3. ESTRELA — registro e designação

**Vocabulário:** registro, designação. Exemplo: “Registro confirmado. Designação em curso.”

**Mecânica nova (3 linhas):**
1. A designação aparece na forma do projétil: ponta, anel ou barra, cada qual com trajetória distinta.
2. Um “titular” espectral registra posições recentes do jogador e percorre o mesmo caminho com atraso fixo.
3. O rastro do titular indica sua próxima passagem; ele se dissipa antes da janela de dano do núcleo.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Duas formas de projétil em ciclos separados; `teleguiado` continua reconhecível. |
| 2: ≤66% e >33% | Titular repete um trecho curto; forma e eco não começam juntos. |
| 3: ≤33% | Três formas no catálogo e um titular por vez; `tudo` é dividido em salvas legíveis. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Ponta, anel e barra | A forma ampliada aparece no boss antes da salva; ponta avança, anel expande, barra atravessa em linha. |
| Titular | Silhueta vazada e pegadas numeradas mostram o trecho gravado e o atraso. |
| `teleguiado` | Retículo contornado acompanha o jogador antes do lançamento, com tom sustentado. |
| `tudo` | Símbolos das formas da próxima salva aparecem em sequência, nunca como brilho único. |

**Como vencer:** reconhecer a forma, sair da trajetória gravada antes do titular e atacar o núcleo no intervalo entre salvas.

**Riscos de balanceamento:** eco punir esquiva recém-feita sem tempo de reação; formas pequenas confundirem projéteis; `tudo` saturar a tela. Limitar um titular, impor atraso observável e manter silhuetas distintas em tamanho mínimo.

**Teste de aceite:** uma mesma sequência de posições gera o mesmo caminho do titular; ele não antecipa entrada futura, o aviso precede o contato e nenhuma salva esconde o jogador ou os demais projéteis.

## 4. PENTAGONO — canal e ruído

**Vocabulário:** canal, ruído. Exemplo: “Canal ocupado. Ruído detectado.”

**Mecânica nova (3 linhas):**
1. A arena se divide em faixas de frequência com símbolos listrados; uma faixa é segura em cada pulso.
2. A estática invade apenas a moldura decorativa do HUD e anuncia a troca de canal, sem cobrir vida, mira ou projéteis.
3. Após cada pulso, o boss abre o canal central e expõe o núcleo por tempo limitado.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Uma faixa ocupada por vez; `mira` indica o ponto de impacto. |
| 2: ≤66% e >33% | Duas faixas ocupadas, com faixa segura contígua; `leque` usa a direção da faixa ativa. |
| 3: ≤33% | Alternância de canal mais frequente, mas nunca durante teletransporte sem aviso; `tudo` em salvas separadas. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Pulso de canal | Listras numeradas no piso e contagem sonora antecedem a faixa atingida. |
| Troca/teletransporte | Silhueta vazada no destino e ruído curto antes de o boss aparecer. |
| `mira` | Retículo com aro que fecha gradualmente no ponto de impacto. |
| `leque` | Cone contornado mostra ângulo e abertura antes dos tiros. |
| `tudo` | Ícones sequenciais das salvas aparecem acima do boss. |

**Como vencer:** ler número e listras da faixa segura, mudar de canal durante a contagem e disparar no núcleo quando o pulso termina.

**Riscos de balanceamento:** ruído esconder informação essencial, canal seguro muito distante, teletransporte sobre a nave. Estática é opcional e removida integralmente em “reduzir efeitos”; símbolos, contagem e abertura continuam visíveis.

**Teste de aceite:** há sempre uma faixa segura alcançável a partir de qualquer posição válida; com “reduzir efeitos”, o jogador recebe os mesmos avisos sem estática; HUD essencial e projéteis permanecem legíveis.

## 5. ANEIS — instância e versão

**Vocabulário:** instância, versão. Exemplo: “Instância ativa. Versão substituída.”

**Mecânica nova (3 linhas):**
1. O boss cria instâncias falsas em outro plano visual, menores e com sombra deslocada; só a instância ativa tem hitbox de boss.
2. A versão ativa muda após um anúncio numerado e uma passagem visível de contorno entre instâncias.
3. Cada troca termina com pausa curta em que a instância ativa pode receber dano; as falsas se desfazem sem colisão surpresa.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Uma falsa e uma ativa; `espiral` parte apenas da ativa. |
| 2: ≤66% e >33% | Duas falsas e uma troca por ciclo; `combinado` tem origem marcada. |
| 3: ≤33% | Troca mais rápida, ainda com anúncio completo; no máximo duas falsas visíveis. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Substituição | Número da versão, contorno contínuo da ativa e linha de transferência antes da troca. |
| `espiral` | Arco segmentado aparece na instância ativa e indica o sentido da primeira volta. |
| `combinado` | Ícones e setores de origem mostram as duas salvas antes do disparo. |

**Como vencer:** seguir o contorno e o número da versão ativa, evitar as salvas indicadas e acertar a instância ativa na pausa pós-troca.

**Riscos de balanceamento:** caça visual frustrante, dano em instância errada parecer inconsistente, falsas encobrirem tiros. A ativa é identificável por forma/contorno e som, nunca só por cor; falsas não bloqueiam projéteis nem o jogador.

**Teste de aceite:** em qualquer frame há exatamente uma instância ativa; a troca é anunciada antes de mudar o alvo válido; matar a ativa remove todas as falsas e emite `BOSS_DEFEATED` uma vez.

## 6. ANEIS DOURADO — garantia e preservação

**Vocabulário:** garantia, preservação. Exemplo: “Garantia mantida. Preservação em curso.”

**Mecânica nova (3 linhas):**
1. Pilares de preservação sustentam um escudo temporário; cada pilar tem símbolo próprio e pode ser desativado.
2. Cada fase retoma uma leitura anterior: rota, nó, canal ou versão, mas usa somente uma delas por ciclo.
3. Com os pilares desativados, o escudo cai por uma janela garantida e o núcleo recebe dano; o ciclo tem limite de repetição.

| Fase por vida | Pressão de arena |
| --- | --- |
| 1: >66% | Dois pilares e uma rota larga; `combinado` dispara após a rota fixar. |
| 2: ≤66% e >33% | Dois pilares e nós numerados; `espiral` preserva acesso ao nó ativo. |
| 3: ≤33% | Três pilares; um canal ou uma troca de versão por ciclo, alternados, com `teleguiado` isolado. |

| Ataque | Telégrafo que independe de cor |
| --- | --- |
| Escudo/pilares | Feixes contínuos ligam pilares ao núcleo; símbolo e número do pilar ativo ficam visíveis antes da proteção. |
| Rota | Bordas tracejadas e seta indicam o corredor antes do bloqueio. |
| Nó | Número grande e forma vazada marcam a próxima tarefa. |
| Canal | Listras numeradas e contagem sonora indicam a faixa atingida. |
| Versão | Número e contorno contínuo identificam a instância ativa antes da troca. |
| `combinado` | Ícones e setores mostram a ordem das salvas. |
| `espiral` | Arco segmentado mostra sentido e abertura inicial. |
| `teleguiado` | Retículo contornado e tom sustentado antecedem o lançamento. |

**Como vencer:** ler a mecânica anunciada, desativar os pilares alcançáveis e atacar o núcleo durante a janela obrigatória de escudo baixo; o último golpe encerra qualquer proteção remanescente.

**Riscos de balanceamento:** recapitulação simultânea virar sobrecarga, invulnerabilidade longa, pilar inacessível por projéteis. Uma mecânica principal por ciclo, tempo máximo de escudo e janela mínima de dano precisam de aceite antes de ajustar vida ou dano.

**Teste de aceite:** cada ciclo permite atingir todos os pilares e abre uma janela finita de dano; nenhuma fase exige boss anterior ou ordem regional; derrota remove escudo/pilares e libera a arena sem travar progressão ou câmera.

## Plano de implementação, sem execução nesta proposta

1. **HEXAGONO, protótipo:** extrair decisão pura de fase, rota segura e agenda de telégrafos; renderizar faixa, seta e sombra em planos 2D; ativar somente no mundo aberto com a opção ligada. Aceitar fuga válida, evento único, câmera fixa e modo clássico intacto antes dos demais bosses.
2. **LOSANGO:** reutilizar agenda de avisos e adicionar sequência pura de nós, reinício ao cruzar corte de vida e verificação de alcance do próximo nó.
3. **ESTRELA:** adicionar histórico limitado de posições e função pura que calcula o caminho atrasado do titular; mapear silhuetas de projétil sem alterar hitboxes existentes.
4. **PENTAGONO:** calcular faixas ocupadas/seguras em lógica pura; separar ruído decorativo do HUD essencial e aplicar “reduzir efeitos”.
5. **ANEIS:** modelar identidade de instância ativa e transição de versão como estado puro; falsas permanecem sem colisão.
6. **ANEIS DOURADO:** compor uma mecânica anterior por ciclo com estado dos pilares, limite de escudo e janela de dano garantida; validar também ordem livre das regiões 2–4.

**Arquivos prováveis, a confirmar na implementação:** `src/runtime/domain/entities/bosses.py` (catálogo/estado); `src/runtime/domain/boss_arena.py` (novo, regras puras); `src/runtime/controllers/boss_arena.py` (novo, encontro e câmera); `src/runtime/domain/world/open_world.py` (entrada/saída da arena, se for o ponto de integração); `src/runtime/controllers/render.py` (planos 2D e avisos, se for o renderizador ativo); `tests/test_boss_arena.py` (novo, lógica pura). Localizar configuração e HUD ativos nessa etapa, sem duplicar eventos, frenagem ou cenas.

**Testes de lógica pura propostos:** cortes de 66%/33% e transição única; opção desligada preserva ataques clássicos; rota segura para cada posição inicial; sequência de nós válida e reiniciável; titular reproduz apenas posições passadas; faixa segura alcançável; uma instância ativa; pilares sempre levam a janela de dano; agenda nunca supera três flashes por segundo. Testes de integração posteriores verificam eventos uma vez, travamento/liberação da câmera, cenas e legibilidade em 900×700 e 1920×1080.
