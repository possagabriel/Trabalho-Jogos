# Protocolos corporativos: minibosses aleatórios

Implementado no runtime de produção, com versão de lançamento sugerida **1.2.0**:
funcionalidade nova, compatível com saves e APIs anteriores. A versão do pacote
não foi alterada; o número pode ser adotado ao publicar a próxima release.

## Arquitetura

```text
src/runtime/
├── domain/entities/minibosses/
│   ├── config.py       # HP, pesos, recompensas, dimensões, tempos e pistas
│   ├── base.py         # Miniboss abstrato, herda Boss
│   ├── registry.py     # decorator registrar + factory criar_miniboss
│   ├── states.py       # Aviso → Ataque → Recuperacao → Aviso
│   ├── strategies.py   # ataques, movimento, proteção e pontos fracos
│   └── types.py        # sete classes registradas
├── domain/systems/miniboss_spawner.py
├── controllers/miniboss.py
└── presentation/miniboss_view.py
tests/test_minibosses.py
tests/test_miniboss_integration.py
```

O projeto executa as entidades de `src/runtime/`; as entidades experimentais de
`src/domain/` ainda não controlam a partida. Por isso a implementação segue a
API ativa `atualizar(jogador, dt)` / `desenhar(tela)` / `rect`. Não há cópia de
lógica em `game/`. A base reutiliza inicialização, vida, flash, hitbox e ataques
simples de `Boss`, que agora aceita configuração opcional, preservando seus
chamadores anteriores. A apresentação desenha silhuetas e telegráficos usando
os helpers de cel-shading existentes e o layout responsivo.

## Catálogo e lore

São protocolos de defesa da megacorporação, executados em cascos que hospedam
cópias de consciências humanas. Cada encontro confronta uma forma de controle
corporativo sobre a IA do jogador.

Os HP abaixo são básicos. A fórmula é `HP × (1 + 0,035 × (nível − 1))`.
Pontos recebem o multiplicador de combo; moedas e o drop são fixos.

| Protocolo | Tema visual | HP | Ataque e mecânica | Como derrotar | Peso | Dimensões | Recompensa: pontos / moedas / drop |
| --- | --- | ---: | --- | --- | ---: | --- | --- |
| Bastião // Firewall | Hexágono ciano, anel de escudo e dois núcleos brancos laterais | 22 | Leque de três tiros; casco imune enquanto existir algum núcleo, cada um com 3 HP | Acertar diretamente os dois núcleos; depois concentrar fogo no centro. Explosões não quebram os núcleos | 10 | 1–6 | 180 / 25 / escudo |
| Espectro // Backdoor | Losango violeta, marca de salto atrás do jogador | 20 | Fixa uma marca por 1,2 s, teleporta e dispara mirando o jogador; volta ao topo após 1 s | Sair da marca e aproveitar o retorno: sempre volta ao alcance dos tiros frontais | 5 | 2–6 | 220 / 30 / arma |
| Matriz // Fork | Pentágono verde com escolta de cópias triangulares | 26 | Leque e invocação de até três scouts; pode repor cópias mortas ou que saíram da tela no ciclo seguinte | Eliminar os lacaios: sem escolta o núcleo recebe dano dobrado | 9 | 1–6 | 200 / 25 / vida |
| Censor // Override | Triângulo magenta e aviso explícito de inversão | 18 | Leque e pulso de 2 s que inverte ambos os eixos de movimento, inclusive controles remapeados | Antecipar o aviso de 1,2 s; aproveitar os 2,5 s de recuperação | 4 | 3–6 | 240 / 35 / escudo |
| Cartógrafo // Quarentena | Quadrado laranja, zonas demarcadas com marcas de contagem | 24 | Leque e duas zonas fixas: uma na posição capturada do jogador e outra na arena; aviso de 1,6 s seguido de perigo por 1,8 s | Sair das marcas antes da ativação; elas não perseguem o jogador | 8 | 1–6 | 210 / 30 / vida |
| Eco // Mirror | Hexágono azul com projéteis da cor da arma copiada | 20 | Reproduz até cinco projéteis do último disparo real, com direções invertidas; trocar a arma sem disparar não muda a cópia | Oferecer tiros simples e desviar do padrão previsto | 6 | 2–6 | 230 / 35 / arma |
| Cronista // Clock | Octógono dourado, anel de blindagem e estado no HUD | 16 | Anel de oito tiros; imune durante 1 s de aviso e 2 s de ataque, vulnerável por 3 s | Guardar rajadas e especial para a janela vulnerável | 3 | 1–6 | 260 / 40 / arma |

As zonas são retângulos: o contorno mostrado é a hitbox real. Seus danos usam
o mesmo escudo e período de invencibilidade do jogador, sem dano acumulado
por sobreposição de zonas. A inversão não altera o arquivo de controles nem
as teclas de tiro, pausa ou especial. A direção de uma esquiva já iniciada é
mantida; novas esquivas usam o vetor invertido.

Eco limita a velocidade da cópia a 4 unidades por frame e o dano ao padrão
inimigo de um acerto. Íon é convertido em bala visível para evitar uma coluna
instantânea de dano na tela inteira. Bombas e Nova copiam aparência/direção,
sem executar explosão de arma aliada. Sem disparo observado, usa leque.

## Configuração do spawner

Os padrões de uma partida ficam em `config.py`:

```python
SPAWN = {"modo": "ondas", "intervalo": 3, "seed": None}
# Alternativa: {"modo": "segundos", "intervalo": 45.0, "seed": 123}
```

No modo ondas, o contador aumenta ao iniciar uma onda comum. Níveis de boss
não contam. O primeiro encontro ocorre na terceira onda comum, e o próximo
exige mais três. Reiniciar a partida reinicia o contador e o histórico de
sorteio; retomar um checkpoint começa uma nova contagem, não usa `nível % N`.

No modo segundos, contam segundos **de simulação**; o runtime atual fornece
`1 / FPS` por atualização, como já faz com os demais elementos do combate.
O loop usa passos fixos e compensa oscilações de FPS dentro do limite de
recuperação da simulação. Pausa,
equipamento, menus, melhorias, hitstop, boss principal e miniboss ativo não
acumulam esse tempo. O intervalo recomeça após encerrar o encontro; não há
fila de encontros atrasados nem múltiplos spawns num mesmo frame.

```python
from src.runtime.domain.systems.miniboss_spawner import MinibossSpawner

spawner = MinibossSpawner(
    modo="segundos", intervalo=45, seed=123,
    pesos={"cronista": 1, "censor": 0},  # zero desabilita
)
```

Pesos não são porcentagens: são normalizados entre tipos registrados,
permitidos na dimensão e diferentes do último sorteado. O tipo anterior é
excluído **antes** do sorteio. Se não houver elegível, adia-se o encontro,
inclusive quando só restar o último tipo. Com essa restrição, mesmo um tipo
de peso muito alto não ultrapassa aproximadamente metade dos encontros.

Cada spawner possui RNG privado. A mesma seed e a mesma sequência de
dimensões/agendamentos produzem a mesma sequência de encontros, sem depender
dos sorteios globais de efeitos visuais. Um segundo fluxo privado atende às
posições das mecânicas; isso evita que elas alterem a seleção seguinte.
Isso não torna todo o jogo determinístico: inimigos legados ainda usam seu
RNG global. O construtor rejeita pesos negativos/não finitos, IDs desconhecidos,
intervalos não positivos e intervalos fracionários no modo ondas.

## Integração já instalada

1. `ControladorProgressao.novo_jogo` chama `miniboss_controller.reiniciar()`.
   `iniciar_nivel` conta ondas comuns e cancela encontros antigos sem recompensa.
2. `Jogo._atualizar_jogando`, depois de verificar o menu de equipamento, chama
   `miniboss_controller.atualizar(1 / FPS)`. O controlador agenda encontros,
   atualiza o estado, transfere projéteis e registra os lacaios na lista de
   inimigos, que já participa do loop e das colisões.
3. `Jogador.atualizar(..., inverter_movimento=...)` recebe o efeito local ao
   encontro. Após `Jogador.atirar()`, `miniboss.observar_tiros(novos)` captura
   o disparo para Eco. O especial também é observado.
4. `ControladorCombate.projetil_jogador_atinge` chama
   `miniboss_controller.receber_tiro(proj)`. As hitboxes dos núcleos são
   verificadas antes do casco. Íon e Gauss preservam a penetração.
5. `explodir_em_area` considera o miniboss ao detonar Nova/Bomba e encaminha
   `receber_area`; dano secundário de plasma também respeita as proteções.
   Contato corporal e zonas usam `colidir_jogador()` e o dano existente.
6. `Jogo._desenhar_jogo` chama `miniboss.desenhar(tela)`. O HUD existente exibe
   nome, barra de vida e fase do encontro, sem disputar espaço com um boss.
7. A condição de fim de onda inclui `not self.miniboss`. Morte do jogador e
   reinício cancelam o encontro. Lacaios e zonas são removidos ao encerrar;
   projéteis que já estavam em voo seguem seu ciclo normal.

Não é preciso colar código em outro entry point: `python main.py` já usa essa
integração. Os módulos são coletados pelo empacotamento Windows existente.

## Persistência e recompensas

A mesclagem recursiva já usada por `SistemaProgressao` adiciona valores padrão
ao carregar saves antigos, preservando moedas, skins, campanha e campos
desconhecidos. Os campos novos são:

```json
{
  "jogador": {"minibosses_derrotados": 0},
  "estatisticas": {
    "minibosses_derrotados": 0,
    "minibosses_por_tipo": {}
  }
}
```

`registrar_miniboss(chave)` incrementa total e tipo. Uma derrota dá pontos,
credita moedas diretamente na loja e salva a contagem e o saldo imediatamente.
As moedas não entram em `moedas_jogo`, evitando duplicação no game over.
A referência ativa é removida antes da recompensa, impedindo crédito repetido
por projéteis simultâneos. Cancelar/transitar/reiniciar não recompensa.
Minibosses não incrementam bosses, não concluem fases e não liberam dimensões.

## Adicionar outro protocolo

Adicione sua entrada em `CATALOGO` com `**PADRAO`, estatísticas e descrição.
Crie a classe e registre-a; não há alteração no spawner, colisões ou loop:

```python
@registrar("auditor")
class Auditor(Miniboss):
    """Novo protocolo de fiscalização."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece o comportamento próprio do auditor."""
        return EstrategiaAuditor()
```

Implemente os hooks necessários de `Estrategia`: `preparar`, `ativar`,
`recuperar`, `mover`, `dano`, `interceptar` e `pontos_fracos`. Se a classe
ficar num módulo separado de `types.py`, importe esse módulo no `__init__.py`
para executar seu decorator. O registro rejeita IDs duplicados ou sem config.

## Testes e balanceamento

Os testes foram escritos e executados primeiro, falhando inicialmente pela
ausência do sistema; depois pelas conexões ainda ausentes no runtime.

```bash
python -m pytest tests/test_minibosses.py tests/test_miniboss_integration.py -q
python -m pytest tests/ -q
```

Cobertura: pesos relativos, seeds, não repetição, filtro por dimensão,
tipos desabilitados, configuração inválida, limite de um vivo, relógio/ondas,
estados e sete mecânicas, tiros diretos/penetrantes/área, zonas e invencibilidade,
lacaios, pausa/equipamento, morte/reinício, migração de save, recompensa única,
prioridade do boss principal, bloqueio de avanço e desenho headless dos estados.

Sugestões para playtest (os valores atuais são um ponto de partida):

- Começar com três ondas ou 45–60 segundos de simulação entre encontros.
- Buscar encontros de 8–15 segundos com arma básica. Ajustar HP por protocolo;
  escudo e invulnerabilidade já prolongam o combate, então evite HP alto neles.
- Manter avisos de pelo menos 1,2 s para teleporte/inversão e 1,6 s para zonas.
- Limitar Matriz a três lacaios; elevar quantidade também aumenta drops e combo.
- Medir dano recebido, mortes e tempo por tipo durante playtests, especialmente
  Censor nas dimensões 3–6. Se punir demais, reduzir o pulso de 2 para 1,5 s.
- Comparar ganho de moedas por minuto; os 25–40 por encontro não devem superar
  a recompensa do boss de dimensão. Ajustar pesos após medir, lembrando que
  a não repetição muda as frequências finais.
