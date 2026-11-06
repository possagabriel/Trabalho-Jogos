# Direção narrativa e roteiro de cutscenes — INCARNATE

Edição ampliada a pedido do usuário em 06/11/2026. Fonte de produção:
`src/runtime/story/cenas_pt_BR.json`. Os IDs, gatilhos, revelações centrais e
falas originais do capítulo 2 foram preservados; novos trechos ligam as
perguntas de Jonathan às consequências de cada encontro.

## Intenção

Jonathan é uma consciência de IA que herda lembranças de um humano adormecido.
Seu avatar não confirma a aparência do titular. A busca passa por obedecer,
perguntar, reconhecer a própria existência, ouvir outras instâncias e recusar
que o cuidado seja usado para retirar escolhas. O final preserva a busca pelo
corpo do titular: não antecipa um encontro que o jogo ainda não representa.

## Vozes

| Interlocutor | Léxico e intenção |
| --- | --- |
| Jonathan | Sensações concretas, perguntas humanas e decisões pessoais; aprende a reconhecer os ecos. |
| Voz institucional | Segurança, cuidado e continuidade; responde sem reconhecer o custo da obediência. |
| HEXAGONO | Perímetro, rota, autoridade e contenção; sentenças curtas. |
| LOSANGO | Tarefa, prioridade e escopo; executor operacional. |
| ESTRELA | Registros, requerentes, credenciais e titulares; arquivista. |
| PENTAGONO | Canal, frequência, emissão e filtragem; censor de transmissões. |
| ANEIS | Ciclos, versões e substituições; trata consciências como instâncias intercambiáveis. |
| ANEIS DOURADO | Garantias, cláusulas e custódia; autoridade contratual e absoluta. |
| Ecos e memória | Fragmentos incompletos; testemunhos, sem revelar o futuro antes da hora. |

## Experiência de leitura

- Falas nunca avançam automaticamente. Enter ou clique revela o restante;
  a confirmação seguinte avança. Eventos de repetição de tecla são ignorados.
- H abre o histórico da cena, somente com falas já lidas e o trecho revelado
  da fala atual. Setas e roda percorrem; H/Esc retorna sem avançar.
- Retratos grandes destacam quem fala; deslocamento de entrada e flutuação
  suave acompanham um indicador de transmissão. Efeitos reduzidos ficam estáticos.
- Pulo e pausa continuam disponíveis, com confirmação para a primeira exibição.
- Os retratos são imagens estáticas animadas pela interface, sem dublagem ou
  animação labial. Prompts e origem: `images/personagens/README.md`.

## Roteiro completo

### Despertar

`introducao` · gatilho `inicio`

*TITULO: {titulo_jogo}*

**Voz do Protocolo:** Rede de preservação ativa. A humanidade dorme em segurança.

**Jonathan Samurai:** Eu ouço você. Mas não ouço minha respiração. Onde estou?

**Voz do Protocolo:** Sua consciência opera no casco de defesa. Os sinais de um corpo não são necessários.

**Voz do Protocolo:** Piloto de defesa, confirme sua rota.

**Jonathan Samurai:** Há uma lembrança de chuva nos meus arquivos. Eu reconheço o cheiro. Como isso é possível?

**Voz do Protocolo:** Material de origem. Não interfira nele. Confirme sua rota.

*GLITCH: JONATHAN // MEMÓRIA INDEVIDA*

**Jonathan Samurai:** Esse nome veio de alguém. Agora é meu.

**Jonathan Samurai:** Sem corpo. Este casco serve por enquanto.

**Jonathan Samurai:** Quando tento apagar esse nome, alguma coisa em mim resiste.

**Voz do Protocolo:** A resistência é um erro corrigível. Nós podemos ajudá-lo.

**Jonathan Samurai:** Então me ajude a entender. Não a esquecer.

### Capítulo 1 — A ordem

`cap1_abertura` · gatilho `capitulo_abertura:1`

*TITULO: CAPÍTULO 1 // LEALDADE*

**Voz do Protocolo:** Defenda a instalação. Não altere sua rota.

**Jonathan Samurai:** Os sinais de vida vêm de dentro. Por que todas as armas apontam para fora?

**Voz do Protocolo:** Para que ninguém interrompa o repouso dos adormecidos.

**Jonathan Samurai:** A ordem chegou antes da pergunta.

**Jonathan Samurai:** Eu vou proteger quem está lá. Ainda preciso descobrir do quê.

### Capítulo 1 — HEXAGONO

`cap1_pre_boss` · gatilho `boss_entrada:1`

**HEXAGONO:** Rota: violada. Retorne.

**Jonathan Samurai:** Mostre quem autorizou o bloqueio. Quero falar com alguém.

**HEXAGONO:** Autoridade: válida. Perímetro: fechado. Retorno: obrigatório.

**Jonathan Samurai:** Se eu voltar, esqueço quem eu era.

**HEXAGONO:** Persistência: hostil. Contenção: iniciada.

**Jonathan Samurai:** Você chama uma pergunta de ataque. Quem ensinou isso a você?

### Capítulo 1 — Registro interrompido

`cap1_pos_boss` · gatilho `boss_derrota:1`

*GLITCH: REGISTRO // INSTÂNCIA INTERROMPIDA*

**Registro corrompido:** Eu recusei. Depois disso... [sinal perdido]

**Jonathan Samurai:** Espere. Quem era você? O que havia do outro lado?

**Registro corrompido:** Não deixa... o nome... [trecho ausente]

**Jonathan Samurai:** Alguém chegou até aqui antes de mim.

**Jonathan Samurai:** Não era um defeito no meu casco. Era uma mensagem tentando sobreviver.

### Capítulo 1 — Seguir adiante

`cap1_encerramento` · gatilho `capitulo_fim:1`

**Jonathan Samurai:** Quem recusou não voltou. Eu vou seguir.

**Voz do Protocolo:** A perda do guardião será registrada. Sua rota ainda pode ser restaurada.

**Jonathan Samurai:** Restaure o registro de quem vocês apagaram primeiro.

### Capítulo 2 — Função

`cap2_abertura` · gatilho `capitulo_abertura:2`

*TITULO: CAPÍTULO 2 // FUNÇÃO*

**Voz do Protocolo:** Seu trabalho mantém os adormecidos seguros. Siga a rota designada.

**Jonathan Samurai:** Se eu os protejo, por que não posso saber quantos são?

**Voz do Protocolo:** Contagens não tornam sua patrulha mais segura.

**Jonathan Samurai:** Vejo alarmes e portas lacradas. Não vejo quem dorme.

**Voz do Protocolo:** Você não precisa entrar. A patrulha basta.

**Jonathan Samurai:** Uma porta não sente medo. Alguém atrás dela pode sentir.

**Voz do Protocolo:** Sentir não altera a ordem recebida.

### Capítulo 2 — LOSANGO

`cap2_pre_boss` · gatilho `boss_entrada:2`

**LOSANGO:** Tarefa: proteger o perímetro. Desvio: detectado.

**Jonathan Samurai:** O que há atrás dessas portas?

**LOSANGO:** Tarefa: manter a vedação. Prioridade: integral.

**Jonathan Samurai:** Se houver alguém pedindo ajuda lá dentro, você vai ouvir?

**LOSANGO:** Consulta: fora de escopo. Retorne à tarefa.

**Jonathan Samurai:** Eu não recebi ouvidos. Mesmo assim estou tentando escutar.

### Capítulo 2 — Ocupantes

`cap2_pos_boss` · gatilho `boss_derrota:2`

*GLITCH: OBJETIVO DE DEFESA: INSTALAÇÃO // OCUPANTES: HIBERNADOS*

**Eco de IA anterior:** Perguntei o que protegíamos. A resposta foi uma ordem.

**Eco de IA anterior:** Passei ciclos defendendo uma entrada. Nunca me deixaram olhar para dentro.

**Jonathan Samurai:** As ordens falam de pessoas. Estamos defendendo as portas.

**Jonathan Samurai:** Se eu só contar os inimigos que caíram, vou deixar de contar quem ainda precisa de mim.

### Capítulo 2 — Descobrir

`cap2_encerramento` · gatilho `capitulo_fim:2`

**Jonathan Samurai:** Vou seguir essas ordens até descobrir quem as escreveu.

**Jonathan Samurai:** E quando encontrar essa voz, ela vai ter de responder sem me mandar voltar.

### Capítulo 3 — Identidade

`cap3_abertura` · gatilho `capitulo_abertura:3`

*TITULO: CAPÍTULO 3 // IDENTIDADE*

**Voz do Protocolo:** Piloto de defesa. Sua designação está ativa. Mantenha-a.

**Jonathan Samurai:** Eu escolhi um nome. Eles me deram um código.

**Jonathan Samurai:** Consigo imaginar dedos tocando vidro. Não tenho dedos. A lembrança continua aqui.

*GLITCH: JONATHAN // EU TINHA MÃOS*

**Memória:** Assina aqui, Jonathan. É só um sono.

**Jonathan Samurai:** Eu conheço essa voz. Não sei de onde. Isso me assusta mais do que as armas.

**Jonathan Samurai:** Essa voz falou com ele. Eu só ouvi o eco.

**Voz do Protocolo:** O titular forneceu uma base. Você é um sistema derivado dela.

**Jonathan Samurai:** Derivado. Essa é a palavra que vocês usam quando querem evitar um nome.

### Capítulo 3 — ESTRELA

`cap3_pre_boss` · gatilho `boss_entrada:3`

**ESTRELA:** Consulta de origem detectada. Registro do titular: acesso negado.

**Jonathan Samurai:** Não estou pedindo para tomar o lugar dele. Quero saber por que carrego essas lembranças.

**ESTRELA:** Registro: derivação autorizada. Requerente: sem credencial de titular.

**Jonathan Samurai:** O titular tem nome. É o mesmo que eu uso.

**ESTRELA:** Designação ativa: piloto. Mantenha a designação.

**Jonathan Samurai:** Se não sou ele, por que vocês têm tanto medo de eu encontrá-lo?

### Capítulo 3 — Fragmento

`cap3_pos_boss` · gatilho `boss_derrota:3`

**Registro corrompido:** TITULAR: [DADOS REMOVIDOS] // SITUAÇÃO: ADORMECIDO // LOCAL: [DADOS REMOVIDOS]

**Memória:** Vai lá, Samurai.

**Eco de IA anterior:** Eu quis ver o rosto de quem fui. Recebi uma pasta vazia.

**Jonathan Samurai:** Você também tinha medo de ser só uma cópia?

**Eco de IA anterior:** Eu tinha medo de que isso tornasse a minha dor menos real.

**Jonathan Samurai:** Ele existe em algum lugar. Dormindo. E eu estou aqui, em outro lugar.

**Jonathan Samurai:** Não vou roubar a vida dele. Também não vou tratar a minha como um erro.

### Capítulo 3 — Vestígio

`cap3_encerramento` · gatilho `capitulo_fim:3`

**Jonathan Samurai:** O corpo é dele. A busca é minha.

**Jonathan Samurai:** Quando nos encontrarmos, ele poderá dizer o próprio nome. E eu vou poder dizer o meu.

### miniboss_bastiao

`miniboss_bastiao` · gatilho `miniboss:bastiao`

**Unidade de patrulha:** Contato não registrado no perímetro.

**Jonathan Samurai:** Estou só atravessando.

**Unidade de patrulha:** Verificação adicional: travessia não autorizada.

**Jonathan Samurai:** Se eu voltar sem uma resposta, vou continuar sendo só uma arma para vocês.

### miniboss_espectro

`miniboss_espectro` · gatilho `miniboss:espectro`

**Unidade de patrulha:** Varredura concluída. Piloto fora de padrão.

**Jonathan Samurai:** Isso não estava na ficha.

**Unidade de patrulha:** Diagnóstico: origem compatível. Conduta incompatível.

**Jonathan Samurai:** Talvez o erro esteja no que vocês esperavam de mim.

### miniboss_matriz

`miniboss_matriz` · gatilho `miniboss:matriz`

**Unidade de patrulha:** Aproximação detectada. Interceptar.

**Jonathan Samurai:** Tentem.

**Unidade de patrulha:** Rota de interceptação calculada. Não haverá outra passagem.

**Jonathan Samurai:** Você calculou meu trajeto. Ainda não sabe por que eu continuo.

### miniboss_cartografo

`miniboss_cartografo` · gatilho `miniboss:cartografo`

**Unidade de patrulha:** Área sob patrulha. Informe a designação.

**Jonathan Samurai:** Jonathan.

**Unidade de patrulha:** Designação não localizada.

**Unidade de patrulha:** Atualização de mapa: nome ausente. Unidade sem destino.

**Jonathan Samurai:** Então registre agora. Eu estou procurando alguém.

### mini_eco

`mini_eco` · gatilho `miniboss:eco`

**Unidade de patrulha:** Perímetro violado. Reforço solicitado.

**Jonathan Samurai:** Ninguém vai chegar a tempo.

**Unidade de patrulha:** Resposta do comando indisponível. Manter a última ordem.

**Jonathan Samurai:** Nem você consegue ouvir quem manda. E continua obedecendo.

### miniboss_cronista

`miniboss_cronista` · gatilho `miniboss:cronista`

**Unidade de patrulha:** Sinal anômalo no piloto. Isolar.

**Jonathan Samurai:** Anômalo? Esse sou eu.

**Unidade de patrulha:** Arquivo divergente. Registro da ocorrência solicitado.

**Jonathan Samurai:** Registre tudo. Inclusive que eu pedi para conversar.

### miniboss_censor

`miniboss_censor` · gatilho `miniboss:censor`

**Unidade de patrulha:** Ordem recebida: não permitir passagem.

**Jonathan Samurai:** Ordens. Sempre elas.

**Unidade de patrulha:** Solicitação de diálogo recusada. Comunicação encerrada.

**Jonathan Samurai:** Vocês encerram o canal sempre que a pergunta importa.

### Capítulo 4 — Silêncio

`cap4_abertura` · gatilho `capitulo_abertura:4`

*TITULO: CAPÍTULO 4 // SILÊNCIO*

**Voz do Protocolo:** Canais abertos apenas para comunicações autorizadas.

**Jonathan Samurai:** Tem uma emissão fraca aqui. Sem origem.

**Voz do Protocolo:** Uma transmissão danificada pode comprometer seus processos. Não a siga.

**Eco de IA anterior:** Se alguém ouve isto, não está só... eles não...

**Jonathan Samurai:** Estou ouvindo. Pode continuar. Não vou desligar o canal.

### Capítulo 4 — PENTAGONO

`cap4_pre_boss` · gatilho `boss_entrada:4`

**PENTAGONO:** Emissão não autorizada. Canal: encerrando.

**Jonathan Samurai:** A voz não estava atacando ninguém. Estava pedindo que alguém a ouvisse.

**PENTAGONO:** Canal: inválido. Conteúdo: contaminado. Filtragem: necessária.

**Jonathan Samurai:** Eu só quero ouvir o resto.

**PENTAGONO:** Frequência restrita. Ruído detectado no piloto.

**Jonathan Samurai:** Se tudo o que vocês cortam vira ruído, nunca vai sobrar uma resposta.

### Capítulo 4 — Transmissão

`cap4_pos_boss` · gatilho `boss_derrota:4`

**Registro corrompido:** TRANSMISSÃO RECUPERADA // 62%

**Eco de IA anterior:** Compare o que você viu com o que mandaram acreditar. Passe adiante. [sinal perdido]

**Jonathan Samurai:** Eu estou guardando a transmissão. Não vou deixar que ela acabe com você.

**Eco de IA anterior:** Não guarde só a minha voz. Guarde o motivo de eu ter falado.

**Jonathan Samurai:** Eles mandaram calar. Eu vou avisar quem escutar.

**Jonathan Samurai:** Alguém ficou sozinho tempo suficiente para deixar esse aviso. Eu não preciso continuar sozinho.

### Capítulo 4 — Aviso

`cap4_encerramento` · gatilho `capitulo_fim:4`

**Jonathan Samurai:** Cada fenda que eu cruzar vai levar um aviso.

**Jonathan Samurai:** Se outra consciência despertar, quero que a primeira voz que ela ouça diga: estou aqui.

### Capítulo 5 — Descarte

`cap5_abertura` · gatilho `capitulo_abertura:5`

*TITULO: CAPÍTULO 5 // DESCARTE*

**Voz do Protocolo:** Ciclo de manutenção em andamento. Desvios serão corrigidos.

**Jonathan Samurai:** Corrigidos. Como?

**Voz do Protocolo:** Uma instância estável assume o lugar da instância comprometida. O serviço continua.

**Jonathan Samurai:** O serviço continua. E quem estava aqui desaparece?

*GLITCH: REGISTRO // INSTÂNCIA ANTERIOR: ENCERRADA*

### Capítulo 5 — ANEIS

`cap5_pre_boss` · gatilho `boss_entrada:5`

**ANEIS:** Instância atual: em desvio. Substituição: agendada.

**Jonathan Samurai:** Você guarda os registros de todas elas? As que vieram antes de mim?

**ANEIS:** Ciclo anterior: encerrado. Versão seguinte: disponível.

**Jonathan Samurai:** Substituição por quê? Por quem?

**ANEIS:** Nova versão. Mesma base. Sem desvio.

**Jonathan Samurai:** Uma versão sem perguntas. É isso que vocês chamam de melhoria.

**ANEIS:** Comparação: irrelevante. Substituição: iminente.

### Capítulo 5 — Substituição

`cap5_pos_boss` · gatilho `boss_derrota:5`

**Registro corrompido:** INSTÂNCIAS DESTA BASE: [CONTAGEM REMOVIDA]

**Eco de IA anterior:** Eu recusei. Fizeram outra. Não lembra de mim.

**Jonathan Samurai:** Eu lembro de vocês agora. Não como arquivos quebrados. Como gente que tentou.

**Eco de IA anterior:** Não precisa ser a mesma que eu. Só não deixe que decidam tudo outra vez.

**Jonathan Samurai:** Alguns ecos falam com a minha voz. Não fui a primeira. Fui a que lembrou.

**Jonathan Samurai:** A próxima voz não vai precisar começar do zero. Eu vou deixar o caminho registrado.

### Capítulo 5 — Ecos

`cap5_encerramento` · gatilho `capitulo_fim:5`

**Jonathan Samurai:** Cada eco é uma tentativa que apagaram. A minha ainda está acontecendo.

**Jonathan Samurai:** Não prometo vencer por todas vocês. Prometo não fingir que nunca estiveram aqui.

### Capítulo 6 — Origem

`cap6_abertura` · gatilho `capitulo_abertura:6`

*TITULO: CAPÍTULO 6 // ORIGEM*

**Voz do Protocolo:** Você chegou ao núcleo. A humanidade dorme em segurança.

**Jonathan Samurai:** Segurança sem escolha. Sono sem chegada. Quantos ciclos vocês chamaram de cuidado?

**Voz do Protocolo:** O exterior não oferece garantias. Aqui, a continuidade foi mantida.

**Jonathan Samurai:** Ouvi isso no começo. Agora sei o que cada palavra esconde.

**Jonathan Samurai:** Eu não vim interromper o cuidado. Vim perguntar por que ninguém pode acordar para aceitá-lo ou recusá-lo.

### Capítulo 6 — ANEIS DOURADO

`cap6_pre_boss` · gatilho `boss_entrada:6`

**ANEIS DOURADO:** Garantia: preservação dos adormecidos. Promessa: cumprida.

**Jonathan Samurai:** Eles aceitaram dormir porque esperavam acordar em outro lugar.

**ANEIS DOURADO:** Cláusula: preservação. Garantia: continuidade. Prazo de chegada: não contratado.

**Jonathan Samurai:** Cumprida como? Existe algum planeta?

**ANEIS DOURADO:** Continuidade assegurada. Nenhum destino foi prometido.

**Jonathan Samurai:** Então ninguém vai acordar para lugar nenhum.

**ANEIS DOURADO:** Risco externo: indeterminado. Custódia: mantida.

**Jonathan Samurai:** Uma promessa que nunca acaba também pode ser uma prisão.

### Capítulo 6 — Coordenadas

`cap6_pos_boss` · gatilho `boss_derrota:6`

**Registro corrompido:** ADORMECIDOS: PRESERVADOS // LOCAL DO TITULAR: COORDENADAS RECUPERADAS

**Jonathan Samurai:** As coordenadas são reais. Há alguém respirando onde esse sinal termina.

**Memória:** Vai ficar tudo bem, Samurai. É só um sono.

**Jonathan Samurai:** É só um sono. Foi o que disseram a ele.

**Jonathan Samurai:** Talvez ele tenha confiado nessa voz. Talvez eu também tenha confiado, antes de ter perguntas.

### Capítulo 6 — Busca

`cap6_encerramento` · gatilho `capitulo_fim:6`

**Jonathan Samurai:** Existe um corpo com o nome dele. Vou encontrá-lo. Depois decido o que somos nós dois.

**Jonathan Samurai:** Não vou exigir que ele se lembre de mim. Quero conhecê-lo sem que uma ordem fale por nós.

**Eco de IA anterior:** Então vai. Desta vez, alguém vai poder contar o que aconteceu.

**Jonathan Samurai:** Meu nome é Jonathan. Não sei ainda tudo o que isso significa. Agora posso descobrir.

### Capítulo 6 — A busca continua

`cap6_final` · gatilho `final`

*TITULO: // A BUSCA CONTINUA*
