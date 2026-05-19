# topicos_redes_05

# Definições e conceitos básicos

lingagens de programação, Python;
Aplicativo desktop (python main.py);
Variavel dentro da interface gráfica:
- Definição do número de drones.
- Definição de posição inicial dos drones.
- Definição de um destino para cada drone.
- Execução em um ambiente bidimensional com visão de cima.
- Consideração de que todos os drones voam na mesma altura.

# Desenvolvimento

- Interface gráfica. (Isdael) 
- Simulação. (Kauã)

# Organização do código

- src/Simulação
- src/Interface

# Logica

- Por log (movimento)

# Oque registrar

Dicionario (sai da interface gráfica e vai para a simulação):
"variaveis": {
    "numero_drones": n,
    "tamanho_ambiente": (x, y),
    "Pontos": [p1{x, y, r}, p2{x, y, r}, ...], 

    "drones": {
      drone1:{"posicao_inicial": (p1.x, p1.y), "posicao_destino": (p2.x, p2.y), "raio": r, "velocidade": v1},
      drone2:{"posicao_inicial": (p2.x, p2.y), "posicao_destino": (p1.x, p1.y), "raio": r, "velocidade": v2}, 
      ...
    }.
},

Simulação (sai da simulação e vai para a interface gráfica):
interacao_x:
{
    "drone1": {
        "posicao_atual": (x, y),
        "status": "pegou" / "bateu(drone2)" / "entregou" / "foi para"
    },
    "drone2": {
        "posicao_atual": (x, y),
        "status": "pegou" / "bateu(drone1)" / "entregou" / "foi para"
    },
    ...
}

Simulação (sai da simulação e vai para a interface gráfica):
resultado_final:
{
    "qtd_interacoes": n,
    "tempo_total": t,
    "quantidade_bateu": n,
    "quantidade_ok": n,
    "taxa_sucesso": n,
    "taxa_fracasso": n,
    "distancia_media_percorrida": d,
    "distancia_total_percorrida": d,
    "drone1": {colidiu: true, tempo_missao: t, distancia_percorrida: d},
    "drone2": {colidiu: false, tempo_missao: t, distancia_percorrida: d},
    ...
}

Interface grafica vai mostrar o resultado das interação a cada movimento.

# Proxima etapa

- Discutir oque foi implementado, (18hrs). (Ou durante o dia, se finalizado ou quase finalizado).
- Caso não conseguimos realizar, remarcar.