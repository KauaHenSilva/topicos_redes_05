import matplotlib.pyplot as plt
import numpy as np

def gerar_e_exibir_graficos(dados_simulacao: dict, resultados_finais: dict):
    """
    Gera e exibe gráficos da simulação baseados nos resultados finais
    usando matplotlib.
    """
    if not resultados_finais:
        return

    # Extrai os nomes dos drones
    drones_nomes = list(dados_simulacao.get("drones", {}).keys())
    
    if not drones_nomes:
        return

    fig = plt.figure(figsize=(12, 8))
    fig.canvas.manager.set_window_title('Resultados da Simulação de Drones')

    # Subplot 1: Status Geral (Pizza)
    ax1 = plt.subplot(2, 2, 1)
    labels_status = ['Sucesso', 'Colisão', 'Não Concluiu']
    
    # Removemos o '%' para converter para float
    sucesso = float(resultados_finais.get("taxa_sucesso", "0%").strip('%'))
    colisao = float(resultados_finais.get("taxa_colisao", "0%").strip('%'))
    fracasso = float(resultados_finais.get("taxa_fracasso", "0%").strip('%'))
    nao_concluiu = fracasso - colisao
    if nao_concluiu < 0: 
        nao_concluiu = 0

    sizes = [sucesso, colisao, nao_concluiu]
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    
    # Filtra zeros para não bugar o pie chart
    sizes_filt = []
    labels_filt = []
    colors_filt = []
    for s, l, c in zip(sizes, labels_status, colors):
        if s > 0:
            sizes_filt.append(s)
            labels_filt.append(l)
            colors_filt.append(c)

    if sizes_filt:
        ax1.pie(sizes_filt, labels=labels_filt, colors=colors_filt, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Taxa de Conclusão Global')

    # Subplot 2: Distância Percorrida por Drone (Bar)
    ax2 = plt.subplot(2, 2, 2)
    distancias = [resultados_finais.get(d, {}).get("distancia_percorrida", 0.0) for d in drones_nomes]
    x_pos = np.arange(len(drones_nomes))
    
    bars = ax2.bar(x_pos, distancias, color='#3498db')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(drones_nomes, rotation=45, ha="right")
    ax2.set_ylabel('Distância (km)')
    ax2.set_title('Distância Percorrida por Drone')
    
    # Adiciona valores no topo das barras
    for bar in bars:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.1f}', va='bottom', ha='center')

    # Subplot 3: Tempo de Missão por Drone (Bar)
    ax3 = plt.subplot(2, 2, 3)
    tempos = [resultados_finais.get(d, {}).get("tempo_missao", 0.0) for d in drones_nomes]
    
    bars_t = ax3.bar(x_pos, tempos, color='#9b59b6')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(drones_nomes, rotation=45, ha="right")
    ax3.set_ylabel('Tempo (horas)')
    ax3.set_title('Tempo de Missão por Drone')
    
    for bar in bars_t:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.1f}', va='bottom', ha='center')

    # Ajusta o layout para não cortar os labels
    plt.tight_layout()
    
    # Mostra a janela do matplotlib sem bloquear a interface principal indefinidamente
    plt.show(block=False)
