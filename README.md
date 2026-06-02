# topicos_redes_05

## Sumário (TOC)

- [Descrição](#descrição)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Onde o cálculo é implementado (trechos de código)](#onde-o-cálculo-é-implementado-trechos-de-código)
- [Funcionalidades](#funcionalidades-capabilities)
- [Por que e como foi implementado (visão de código)](#por-que-e-como-foi-implementado-visão-de-código)
- [Core (núcleo)](#core-núcleo---explicação-por-código)
- [Dúvidas de arquitetura (simuladas)](#dúvidas-de-arquitetura-simuladas)
- [FAQ](#dúvidas-comuns-faq)
- [Execução](#execução)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Formato de entrada e saída](#formato-de-entrada-e-saída)
- [Contribuição](#contribuição)
- [Arquivo principal](#arquivo-principal)

---

## Descrição

Projeto de simulação de múltiplos drones em um ambiente bidimensional (visão de cima). A aplicação é escrita em Python e combina uma interface gráfica com um núcleo de simulação que recebe parâmetros via arquivos JSON e gera logs de interação e um resultado final resumido.

## Requisitos

- Python 3.10+ (recomendado). Testado em Windows.
- Virtual environment (`venv`) ou similar.
- Dependências listadas em `requirements.txt`.

## Instalação

Exemplo (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Exemplo (Unix/macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Como a colisão entre dois drones é detectada no código?

- Onde: `_detectar_colisoes` em [src/simulacao/simulador.py](src/simulacao/simulador.py#L219) e `distancia` em [src/simulacao/modelos.py](src/simulacao/modelos.py#L71).

- O que faz: compara a posição dos centros dos dois drones; se a distância ≤ soma dos `raio`s (mais `EPSILON`) marca colisão e registra evento.

- Por quê: verificação por sobreposição de áreas (discos) é simples, determinística e suficiente para colisões 2D.

### Como a colisão com uma parede/zona é detectada e tratada?

- Onde: `distancia_ponto_segmento` em [src/simulacao/modelos.py](src/simulacao/modelos.py#L75) e uso em [src/simulacao/simulador.py](src/simulacao/simulador.py#L171).

- O que faz: mede a menor distância do centro do drone ao segmento que representa a parede; se ≤ `drone.raio` considera toque. Em caso de toque, usa `parede.probabilidade` e `random.random()` para decidir crash ou sobrevivência (registra imunidade se sobrevive).

- Por quê: trata paredes finitas corretamente e incorpora comportamento probabilístico definido pelo cenário.

### Como o sistema marca oficialmente que um drone colidiu (estado e registros)?

- Onde: `_detectar_colisoes` em [src/simulacao/simulador.py](src/simulacao/simulador.py#L219).

- O que faz: seta `drone.colidiu = True`, atualiza `drone.status` (ex.: `"bateu(...)"`) e `drone.tempo_missao = tempo_atual`; adiciona evento textual ao log da iteração.

- Por quê: flags no objeto `Drone` tornam o estado acessível para agregação final, interface e testes.

### Como o simulador determina a interseção entre segmentos (por exemplo rota × parede)?

- Onde: `intersecao_segmentos` em [src/simulacao/modelos.py](src/simulacao/modelos.py#L117) (função de utilidade usada no simulador).

- O que faz: verifica se dois segmentos se cruzam; se sim retorna o ponto (x,y), caso contrário `None`. O simulador usa esse ponto para estimar se a rota cruza uma parede.

- Por quê: considerar apenas interseções dentro dos segmentos evita falsos positivos de linhas infinitas.

### Como o simulador estima o tempo até um evento (colisão/entrega) para avançar por eventos?

- Onde: `_calcular_tempo_ate_proximo_evento`, `_tempo_ate_entrega`, `_tempo_ate_colisao`, `_tempo_ate_colisao_parede` em [src/simulacao/simulador.py](src/simulacao/simulador.py#L1).

- O que faz: cada função estima quando um evento pode ocorrer a partir das posições e vetores de velocidade; `_calcular_tempo_ate_proximo_evento` reúne as estimativas e retorna o menor tempo positivo para avançar a simulação.

- Por quê: avançar por eventos (pular tempo ocioso) melhora performance e mantém o log preciso por evento.

### Como os eventos são registrados para a interface e para os arquivos de saída (logs)?

- Onde: `executar()` monta `interacoes` e `eventos_interacoes`; `_detectar_colisoes` e `_marcar_entregas` adicionam eventos; `_resultado_final` agrega e formata o resumo ([src/simulacao/simulador.py](src/simulacao/simulador.py#L1)).

- O que faz: cada iteração produz `interacao_N` com posições e eventos textuais; ao final `_resultado_final` gera o dicionário pronto para salvar em JSON em `saida/`.

- Por quê: eventos textuais são legíveis pela interface e fáceis de serializar para análise posterior.

### Como tornar a simulação reproduzível entre execuções (controle de RNG/semente)?

- Onde: o simulado usa `random.random()` (ex.: decisões de parede) em [src/simulacao/simulador.py](src/simulacao/simulador.py#L171).

- O que fazer: definir `random.seed(<valor>)` no `main.py` ou carregar `seed` do `config.json` antes de instanciar o simulador.

- Por quê: controlar a semente torna execuções determinísticas para o mesmo cenário, essencial para testes e comparações.

```py
t = self._tempo_ate_colisao(drone_a, drone_b)
if t is not None and t > EPSILON:
    candidatos.append(t)
```

### _tempo_ate_colisao_parede

- Arquivo: [src/simulacao/simulador.py](src/simulacao/simulador.py#L161)

```py
intersecao = intersecao_segmentos(pos_atual, drone.destino, parede.p1, parede.p2)
dist = max(0.0, distancia(pos_atual, intersecao) - drone.raio)
return dist / drone.velocidade
```

- O que faz: verifica se a trajetória do drone cruza o segmento da parede; se sim, estima o tempo até contato com base na distância até o ponto de interseção (ajustada pelo `drone.raio`).
- Como é usado: chamado para cada parede relevante ao montar os tempos candidatos em `_calcular_tempo_ate_proximo_evento()`.
- Exemplo (pseudocódigo):

```py
t_parede = self._tempo_ate_colisao_parede(drone, parede)
if t_parede is not None and t_parede > EPSILON:
    candidatos.append(t_parede)
```

- `_vetor_velocidade` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L183)

```py
return ((destino_x - origem_x) / distancia_restante * drone.velocidade,
        (destino_y - origem_y) / distancia_restante * drone.velocidade)
```

O que faz: calcula o vetor de velocidade (direção normalizada vezes velocidade escalar).

Por que: separar cálculo de direção facilita testes e reuso em cálculo de tempo/posições.

- `_mover_drone` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L197)

```py
deslocamento = min(drone.velocidade * delta_tempo, distancia_restante)
nova_posicao = (origem_x + (destino_x - origem_x) * fator, ...)
drone.posicao_atual = nova_posicao
drone.distancia_percorrida += deslocamento
```

O que faz: atualiza `drone.posicao_atual` e acumula `drone.distancia_percorrida`.

Por que: garante que o drone não ultrapasse o destino e mantém métricas precisas.

- `_detectar_colisoes` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L219)

```py
if distancia(drone_a.posicao_atual, drone_b.posicao_atual) <= (drone_a.raio + drone_b.raio) + EPSILON:
    # marca envolvidos e cria eventos
```

O que faz: detecta colisões imediatas entre pares de drones e com paredes, marca estado e gera eventos.

Por que: detecção centralizada produz eventos textuais usados pela interface e pelo `resultado_final`.

- `_resultado_final` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L295)

```py
distancia_total = sum(drone.distancia_percorrida for drone in self.drones.values())
resultado["distancia_media_percorrida"] = self._arredondar(distancia_total / total)
```

O que faz: agrega métricas finais a partir do estado de cada `Drone` (distâncias, tempos, taxas, etc.).

Por que: separa a lógica de resumo dos detalhes de simulação, produzindo um JSON `resultado_final` fácil de analisar.

- `encontrar_base_proxima` — [src/interface/telas/tela_mapa.py](src/interface/telas/tela_mapa.py#L604)

```py
distancia = math.hypot(px_x - base_px_x, px_y - base_px_y)
```

O que faz: calcula distância em pixels para detectar cliques em bases no mapa.

Por que: centraliza conversão km↔pixels e mantém a interface responsiva a cliques do usuário.

Se quiser, eu posso substituir cada trecho acima por um link direto para a linha exata do arquivo (com números de linha precisos), ou incluir exemplos de uso (pequenos snippets de como chamar as funções no REPL). Deseja que eu adicione esses links linha-a-linha ou mantenha a seção assim?

**Funcionalidades (capabilities)**

- Definir número de drones e parâmetros individuais (posições, destinos, raio, velocidade).
- Simular movimento contínuo/discreto em ambiente 2D com atualizações por passo.
- Detectar colisões entre drones por sobreposição de raios.
- Gerar logs de cada interação para reprodução e visualização na interface.
- Agregar métricas finais: tempo total, distâncias percorridas, taxas de sucesso/fracasso.

**Por que e como foi implementado (visão de código)**

Esta seção explica, em termos de código e arquitetura, as decisões de implementação e o motivo de cada componente existir — sem entrar em fórmulas matemáticas.

- Arquitetura separada por responsabilidades: a interface gráfica fica em `src/interface/` e o motor de simulação em `src/simulacao/`. Isso facilita testes, manutenção e permitir usar a simulação sem interface.
- Modelos e estado: entidades como `Drone`, `Ponto` e `Parede` são `dataclass` em [src/simulacao/modelos.py](src/simulacao/modelos.py#L1). `Ponto` é imutável (`frozen=True`) porque representa referências fixas no mapa; `Drone` guarda estado mutável da missão (posição, distância percorrida, status).
- Motor orientado a eventos: o núcleo em [src/simulacao/simulador.py](src/simulacao/simulador.py#L1) é um simulador orientado a eventos que calcula o tempo até o próximo evento (`_calcular_tempo_ate_proximo_evento`) e avança a simulação por saltos discretos. Isso evita passos fixos pequenos e melhora desempenho em cenários esparsos.
- Funções pequenas e reutilizáveis: operações de utilidade (distância, intersecção de segmentos, distância ponto–segmento) estão em `modelos.py` e são chamadas pelo simulador. Isso mantém a lógica testável e separada da lógica de alto nível.
- Movimento e direção: `_vetor_velocidade` calcula o vetor-velocidade por drone e `_mover_drone` aplica o deslocamento mínimo entre o disponível e o que falta até o destino, atualizando `posicao_atual` e `distancia_percorrida` do `Drone`.
- Detecção e registro de eventos: `_detectar_colisoes` identifica colisões imediatas entre drones e com paredes, marca o estado dos drones (`colidiu`, `status`) e produz eventos textuais armazenados em `eventos_interacoes` para posterior análise ou exibição.
- Agregação de métricas: `_resultado_final` recolhe métricas a partir do estado final dos `Drone`s (distâncias percorridas, quantidades de colisões/entregas, tempos), usando helpers locais para arredondamento e formatação.
- Configuração por JSON: cenários e parâmetros são carregados a partir de arquivos em `config/`, permitindo reproduzir execuções e comparar resultados sem recompilar código.
- Testabilidade e manutenção: design modular e uso de pequenos helpers tornam possível escrever testes unitários para cada função (ex.: `distancia`, `distancia_ponto_segmento`, `_tempo_ate_colisao`) sem depender da interface.
- Logs e reprodutibilidade: cada iteração gera `interacao_N.json` em `saida/`, e o `resultado_final.json` resume métricas — isso facilita reprodução, depuração e geração de gráficos externos.

Core (núcleo) — explicação por código

Abaixo estão as rotinas centrais do `SimuladorDrones` com explicações do que fazem e por que foram implementadas dessa forma. Foquei apenas no core da simulação, sem funções auxiliares.

- `executar()` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L1)

```py
def executar(self) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    # loop principal que avança por eventos e produz interações + resultado final
```

O que faz: gerencia o estado global da simulação, inicializa logs, executa o loop de eventos e devolve as interações e o resumo final.

Por que: concentrar o controle de fluxo num único método facilita observar o estado e exportar logs para a interface.

- `_calcular_tempo_ate_proximo_evento()` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L1)

```py
def _calcular_tempo_ate_proximo_evento(self) -> float | None:
    # consulta tempos de entrega, colisões entre drones e colisões com paredes
```

O que faz: agrega estimativas de quando ocorrerá o próximo evento relevante e retorna o menor tempo positivo.

Por que: abordagem orientada a eventos evita passos fixos desnecessários, melhorando desempenho em cenários com poucos eventos.

- `_tempo_ate_entrega(drone)` e `_tempo_ate_colisao(drone_a, drone_b)` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L1)

```py
def _tempo_ate_entrega(self, drone): ...
def _tempo_ate_colisao(self, drone_a, drone_b): ...
```

O que fazem: calculam, para cada drone ou par de drones, quando um evento (entrega ou colisão) pode ocorrer.

Por que: separar cálculos por tipo de evento mantém o código modular e permite priorizar eventos críticos.

- `_mover_drone(drone, delta_tempo, tempo_atual)` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L197)

```py
def _mover_drone(self, drone, delta_tempo, tempo_atual) -> None:
    # aplica deslocamento limitado ao que falta até o destino e atualiza métricas
```

O que faz: alterna a posição do drone com base no tempo decorrido até o próximo evento e acumula distância percorrida.

Por que: garante que drones não "pulem" destinos e mantém medidas coerentes para relatórios.

- `_detectar_colisoes(tempo_atual)` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L219)

```py
def _detectar_colisoes(self, *, tempo_atual: float) -> list[str]:
    # detecta colisões entre drones e com paredes, marca estados e gera eventos textuais
```

O que faz: identifica colisões imediatas, define `drone.colidiu` e popula a lista de eventos da iteração.

Por que: eventos textuais servem tanto para a interface quanto para o `resultado_final`, consolidando sinalização de falhas.

- `_resultado_final(...)` — [src/simulacao/simulador.py](src/simulacao/simulador.py#L295)

```py
def _resultado_final(self, iteracoes, tempo_total, tempos_interacoes, eventos_interacoes) -> dict:
    # agrega métricas a partir do estado dos drones e retorna dicionário pronto para JSON
```

O que faz: reúne métricas (tempos, distâncias, quantidades de colisões/entregas) e formata o resultado final.

Por que: separar a agregação do loop principal deixa `executar()` focado no avanço da simulação e facilita testes do resumo.

---

Se quiser que eu deixe ainda mais direto (apenas as assinaturas de métodos em ordem e comentários inline), eu reduzo para um bloco enxuto. Deseja versão enxuta? 



**Dúvidas comuns (FAQ)**

- Como `r` é usado? : `r` é o raio de ocupação do drone; o código que usa `r` está em `_detectar_colisoes` (marca colisões) e em `distancia_ponto_segmento` (verifica proximidade a paredes).
- Como é calculada a distância média? : a distância média por drone é calculada em `_resultado_final` a partir de `drone.distancia_percorrida` para cada `Drone`.
- Como é calculado o tempo total da simulação? : o `SimuladorDrones` acumula `tempo_atual` ao avançar eventos; o valor final aparece em `resultado_final["tempo_total"]`.

**Executando testes**

Se houver testes automatizados, rode:

```bash
pytest -q
```

**Contribuição**

1. Abra uma issue com a proposta.
2. Crie uma branch com a feature/bugfix.
3. Envie um pull request com descrição clara das mudanças.

**Arquivo principal**

Veja o ponto de entrada em [main.py](main.py).

---

Se quiser, eu ajusto exemplos concretos (valores numéricos) para os cenários em `config/` ou adiciono seções sobre visualização/plots dos resultados (ex.: gráficos de distância ao longo do tempo). Deseja que eu gere isso também?