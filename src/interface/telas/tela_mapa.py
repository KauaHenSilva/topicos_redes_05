import math
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

import customtkinter as ctk
from tkinter import Canvas, TclError, filedialog, messagebox

from src.interface.utils.gerador_json import (
    carregar_configuracao_interface,
    preparar_dados_interface,
    salvar_configuracao_interface,
)
from src.simulacao import executar_simulacao as executar_motor_simulacao
from src.simulacao import salvar_resultado


class TelaMapa:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.modo_atual = None  
        self.base_origem_temp = None  
        self.id_circulo_selecao = None 
        
        self.canvas_items = {"bases": {}, "drones": {}}
        self.item_selecionado = {"tipo": None, "nome": None}
        self.interacoes_simulacao: dict[str, dict[str, dict[str, Any]]] = {}
        self.resultado_final_simulacao: dict[str, Any] | None = None
        self.nomes_interacoes: list[str] = []
        self.indice_interacao_atual = 0
        self.pasta_resultado_simulacao: Path | None = None
        self.quadros_timeline: list[tuple[str, float, dict[str, dict[str, Any]]]] = []
        self.tempo_animacao_atual = 0.0
        self.tempo_total_animacao = 0.0
        self.animacao_rodando = False
        self.animacao_after_id = None
        self.ultimo_tick_animacao = 0.0
        self.atualizando_timeline = False
        
        self.construir_tela()

    def construir_tela(self):
        self.painel_lateral = ctk.CTkFrame(self.parent, width=280)
        self.painel_lateral.pack(side="right", fill="y", padx=10, pady=10)

        lbl_ferramentas = ctk.CTkLabel(self.painel_lateral, text="Ferramentas", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_ferramentas.pack(pady=(15, 10))

        self.btn_modo_base = ctk.CTkButton(self.painel_lateral, text="Criar Base (Ponto)", fg_color="green", command=self.ativar_modo_base)
        self.btn_modo_base.pack(pady=5, padx=20)

        self.btn_modo_drone = ctk.CTkButton(self.painel_lateral, text="Criar Drone", command=self.ativar_modo_drone)
        self.btn_modo_drone.pack(pady=5, padx=20)

        self.btn_carregar_config = ctk.CTkButton(
            self.painel_lateral,
            text="Carregar Configuração",
            fg_color="#555555",
            hover_color="#333333",
            command=self.carregar_configuracao,
        )
        self.btn_carregar_config.pack(pady=(14, 5), padx=20)

        self.btn_salvar_config = ctk.CTkButton(
            self.painel_lateral,
            text="Salvar Configuração Como",
            fg_color="orange",
            hover_color="#cc7000",
            command=self.salvar_configuracao_como,
        )
        self.btn_salvar_config.pack(pady=5, padx=20)

        self.btn_pasta_saida = ctk.CTkButton(
            self.painel_lateral,
            text="Escolher Pasta de Saída",
            fg_color="#555555",
            hover_color="#333333",
            command=self.escolher_pasta_saida,
        )
        self.btn_pasta_saida.pack(pady=5, padx=20)

        self.lbl_pasta_saida = ctk.CTkLabel(
            self.painel_lateral,
            text="Saída: saida",
            text_color="gray",
            wraplength=220,
            justify="center",
        )
        self.lbl_pasta_saida.pack(pady=(0, 8), padx=20)
        self.atualizar_label_pasta_saida()

        self.lbl_status = ctk.CTkLabel(self.painel_lateral, text="Modo: Visualização", text_color="gray")
        self.lbl_status.pack(pady=10)

        lbl_lista = ctk.CTkLabel(self.painel_lateral, text="Elementos Criados", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_lista.pack(pady=(10, 5))
        
        self.scroll_lista = ctk.CTkScrollableFrame(self.painel_lateral, height=200)
        self.scroll_lista.pack(fill="both", expand=True, padx=10, pady=5)

        self.caixa_resultado = ctk.CTkTextbox(self.painel_lateral, height=150)
        self.caixa_resultado.pack(fill="x", padx=10, pady=(5, 10))
        self.caixa_resultado.insert("1.0", "Resultado da simulação aparecerá aqui.")
        self.caixa_resultado.configure(state="disabled")

        self.btn_voltar = ctk.CTkButton(self.painel_lateral, text="Voltar à Configuração", fg_color="#555555", hover_color="#333333", command=self.voltar)
        self.btn_voltar.pack(side="bottom", pady=(10, 15), padx=20)

        self.btn_exportar = ctk.CTkButton(self.painel_lateral, text="Exportar JSON", fg_color="orange", hover_color="#cc7000", command=self.exportar_json)
        self.btn_exportar.pack(side="bottom", pady=5, padx=20)

        self.frame_mapa = ctk.CTkFrame(self.parent)
        self.frame_mapa.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.canvas = Canvas(self.frame_mapa, bg="#2b2b2b", highlightthickness=1, highlightbackground="#555555")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        self.canvas.bind("<Button-1>", self.registrar_clique)

        self.canvas.bind("<Configure>", self.redesenhar_mapa)

        self.frame_timeline = ctk.CTkFrame(self.frame_mapa)
        self.frame_timeline.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_simular = ctk.CTkButton(
            self.frame_timeline,
            text="Simular",
            width=110,
            fg_color="#7d3c98",
            hover_color="#5b2c6f",
            command=self.alternar_animacao,
        )
        self.btn_simular.pack(side="left", padx=(10, 8), pady=10)

        self.timeline_slider = ctk.CTkSlider(
            self.frame_timeline,
            from_=0,
            to=1,
            command=self.arrastar_timeline,
        )
        self.timeline_slider.set(0)
        self.timeline_slider.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_tempo_timeline = ctk.CTkLabel(
            self.frame_timeline,
            text="t=0 / 0",
            width=90,
        )
        self.lbl_tempo_timeline.pack(side="left", padx=8)

        self.lbl_interacao = ctk.CTkLabel(
            self.frame_timeline,
            text="Sem simulação",
            width=260,
            wraplength=250,
            justify="left",
            anchor="w",
        )
        self.lbl_interacao.pack(side="left", padx=(4, 10), pady=8)

        self.atualizar_lista_painel()

    # ================== FUNÇÕES DE CONVERSÃO (MÁGICA DA ESCALA) ==================
    def pixels_para_km(self, px_x, px_y):
        largura_canvas = self.canvas.winfo_width()
        altura_canvas = self.canvas.winfo_height()
        largura_km, altura_km = self.app.dados_simulacao["tamanho_ambiente"]

        # Evita divisão por zero se a janela ainda não renderizou completamente
        if largura_canvas <= 1 or altura_canvas <= 1:
            return px_x, px_y

        km_x = (px_x * largura_km) / largura_canvas
        km_y = (px_y * altura_km) / altura_canvas
        return round(km_x, 2), round(km_y, 2)

    def km_para_pixels(self, km_x, km_y):
        largura_canvas = self.canvas.winfo_width()
        altura_canvas = self.canvas.winfo_height()
        largura_km, altura_km = self.app.dados_simulacao["tamanho_ambiente"]

        px_x = (km_x * largura_canvas) / largura_km
        px_y = (km_y * altura_canvas) / altura_km
        return px_x, px_y

    def raio_km_para_pixels(self, raio_km):
        largura_canvas = self.canvas.winfo_width()
        altura_canvas = self.canvas.winfo_height()
        largura_km, altura_km = self.app.dados_simulacao["tamanho_ambiente"]

        if largura_km <= 0 or altura_km <= 0:
            return 0.0, 0.0

        return (
            abs((float(raio_km) * largura_canvas) / largura_km),
            abs((float(raio_km) * altura_canvas) / altura_km),
        )
    
    def redesenhar_mapa(self, event=None):
        # Limpa todos os desenhos visuais atuais do Canvas
        self.canvas.delete("all")
        
        # Opcional: Você pode querer manter os IDs velhos atualizados ou recriá-los. 
        # A forma mais segura é recriar o dicionário visual.
        self.canvas_items = {"bases": {}, "drones": {}}

        # 1. Redesenha todas as Bases
        for nome_base, dados in self.app.dados_simulacao["Pontos"].items():
            px_x, px_y = self.km_para_pixels(dados["x"], dados["y"])
            raio_visual = 10 
            
            # Recria a base e salva os novos IDs
            id_oval = self.canvas.create_oval(px_x - raio_visual, px_y - raio_visual, px_x + raio_visual, px_y + raio_visual, fill="#2ecc71", outline="white")
            id_texto = self.canvas.create_text(px_x, px_y + 20, text=nome_base, fill="white", font=("Arial", 12, "bold"))
            self.canvas_items["bases"][nome_base] = {"oval": id_oval, "texto": id_texto}

        # 2. Redesenha todos os Drones
        for nome_drone, dados in self.app.dados_simulacao["drones"].items():
            p1_km = self.app.dados_simulacao["Pontos"][dados["posicao_inicial"]]
            p2_km = self.app.dados_simulacao["Pontos"][dados["posicao_destino"]]
            
            p1_px_x, p1_px_y = self.km_para_pixels(p1_km["x"], p1_km["y"])
            p2_px_x, p2_px_y = self.km_para_pixels(p2_km["x"], p2_km["y"])
            
            id_linha = self.canvas.create_line(p1_px_x, p1_px_y, p2_px_x, p2_px_y, arrow="last", fill="#1f6aa5", width=2, dash=(4, 4))
            meio_x, meio_y = (p1_px_x + p2_px_x) / 2, (p1_px_y + p2_px_y) / 2
            id_texto = self.canvas.create_text(meio_x, meio_y - 10, text=nome_drone, fill="#1f6aa5", font=("Arial", 10, "bold"))
            self.canvas_items["drones"][nome_drone] = {"linha": id_linha, "texto": id_texto}
            
        # Se havia algo selecionado na lista, destaca novamente
        if self.item_selecionado["tipo"]:
             self.destacar_no_mapa(self.item_selecionado["tipo"], self.item_selecionado["nome"])

        if self.quadros_timeline:
            self.mostrar_tempo_simulacao(
                self.tempo_animacao_atual,
                atualizar_slider=False,
            )

    # ================== LÓGICA DE LISTA E SELEÇÃO ==================
    def atualizar_lista_painel(self):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        total_pontos = len(self.app.dados_simulacao["Pontos"])
        total_drones = len(self.app.dados_simulacao["drones"])

        lbl_bases = ctk.CTkLabel(
            self.scroll_lista,
            text=f"Bases / Pontos ({total_pontos})",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2ecc71",
        )
        lbl_bases.pack(fill="x", padx=6, pady=(4, 2))

        for nome_base, dados_base in self.app.dados_simulacao["Pontos"].items():
            texto_base = f"Base: {nome_base} (r={dados_base.get('r', 0)})"
            btn = ctk.CTkButton(self.scroll_lista, text=texto_base, anchor="w", fg_color="transparent", 
                                text_color="white", hover_color="#444444", 
                                command=lambda n=nome_base: self.clicar_item_lista("base", n))
            btn.pack(fill="x", pady=2)

        if not self.app.dados_simulacao["Pontos"]:
            lbl_vazio_bases = ctk.CTkLabel(
                self.scroll_lista,
                text="Nenhuma base criada",
                anchor="w",
                text_color="gray",
            )
            lbl_vazio_bases.pack(fill="x", padx=14, pady=(0, 8))

        lbl_drones = ctk.CTkLabel(
            self.scroll_lista,
            text=f"Drones / Rotas ({total_drones})",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db",
        )
        lbl_drones.pack(fill="x", padx=6, pady=(12, 2))

        for nome_drone, dados_drone in self.app.dados_simulacao["drones"].items():
            raio = dados_drone.get("raio", 0)
            texto_drone = f"Drone: {nome_drone} (r={raio})"
            btn = ctk.CTkButton(self.scroll_lista, text=texto_drone, anchor="w", fg_color="transparent", 
                                text_color="white", hover_color="#444444", 
                                command=lambda n=nome_drone: self.clicar_item_lista("drone", n))
            btn.pack(fill="x", pady=2)

        if not self.app.dados_simulacao["drones"]:
            lbl_vazio_drones = ctk.CTkLabel(
                self.scroll_lista,
                text="Nenhum drone criado",
                anchor="w",
                text_color="gray",
            )
            lbl_vazio_drones.pack(fill="x", padx=14, pady=(0, 4))

    def clicar_item_lista(self, tipo, nome):
        if self.item_selecionado["tipo"] == tipo and self.item_selecionado["nome"] == nome:
            if tipo == "base":
                self.abrir_formulario_base(km_x=0, km_y=0, editando_nome=nome)
            elif tipo == "drone":
                self.abrir_formulario_drone(origem=None, destino=None, editando_nome=nome)
        else:
            self.item_selecionado = {"tipo": tipo, "nome": nome}
            self.destacar_no_mapa(tipo, nome)

    def destacar_no_mapa(self, tipo, nome):
        for n, items in self.canvas_items["bases"].items():
            self.canvas.itemconfig(items["oval"], outline="white", width=1)
        for n, items in self.canvas_items["drones"].items():
            self.canvas.itemconfig(items["linha"], fill="#1f6aa5", width=2)
            self.canvas.itemconfig(items["texto"], fill="#1f6aa5")

        if tipo == "base" and nome in self.canvas_items["bases"]:
            id_oval = self.canvas_items["bases"][nome]["oval"]
            self.canvas.itemconfig(id_oval, outline="yellow", width=3)
        elif tipo == "drone" and nome in self.canvas_items["drones"]:
            id_linha = self.canvas_items["drones"][nome]["linha"]
            id_texto = self.canvas_items["drones"][nome]["texto"]
            self.canvas.itemconfig(id_linha, fill="yellow", width=4)
            self.canvas.itemconfig(id_texto, fill="yellow")

    # ================== LÓGICA DE CLIQUE NO MAPA ==================
    def ativar_modo_base(self):
        self.limpar_selecao_visual()
        self.modo_atual = "base"
        self.base_origem_temp = None
        self.lbl_status.configure(text="Modo: Clique no mapa para criar uma base", text_color="green")

    def ativar_modo_drone(self):
        self.limpar_selecao_visual()
        self.modo_atual = "drone"
        self.base_origem_temp = None
        self.lbl_status.configure(text="Modo: Selecione a base de Origem", text_color="#1f6aa5")

    def registrar_clique(self, event):
        px_x, px_y = event.x, event.y
        km_x, km_y = self.pixels_para_km(px_x, px_y)

        if self.modo_atual == "base":
            self.abrir_formulario_base(km_x, km_y)
        elif self.modo_atual == "drone":
            self.logica_clique_drone(px_x, px_y)

    def encontrar_base_proxima(self, px_x, px_y):
        for nome_base, coords in self.app.dados_simulacao["Pontos"].items():
            # Converte a posição guardada em km de volta para pixel para calcular a colisão com o mouse
            base_px_x, base_px_y = self.km_para_pixels(coords["x"], coords["y"])
            distancia = math.hypot(px_x - base_px_x, px_y - base_px_y)
            if distancia <= 35:  
                return nome_base
        return None

    def limpar_selecao_visual(self):
        if self.id_circulo_selecao:
            self.canvas.delete(self.id_circulo_selecao)
            self.id_circulo_selecao = None
        self.item_selecionado = {"tipo": None, "nome": None}
        self.destacar_no_mapa(None, None) 

    def logica_clique_drone(self, px_x, px_y):
        base_clicada = self.encontrar_base_proxima(px_x, px_y)
        if not base_clicada:
            messagebox.showwarning("Aviso", "Você precisa clicar em cima de uma base criada!")
            return

        if self.base_origem_temp is None:
            self.base_origem_temp = base_clicada
            self.lbl_status.configure(text=f"Origem: {base_clicada}. Clique no Destino.", text_color="orange")
            coords = self.app.dados_simulacao["Pontos"][base_clicada]
            base_px_x, base_px_y = self.km_para_pixels(coords["x"], coords["y"])
            self.id_circulo_selecao = self.canvas.create_oval(base_px_x - 18, base_px_y - 18, base_px_x + 18, base_px_y + 18, outline="orange", width=2, dash=(4, 4))
        else:
            base_destino = base_clicada
            if base_destino == self.base_origem_temp:
                messagebox.showwarning("Aviso", "O destino não pode ser igual à origem!")
                self.ativar_modo_visualizacao()
                return
            
            self.abrir_formulario_drone(self.base_origem_temp, base_destino)

    def ativar_modo_visualizacao(self):
        self.modo_atual = None
        self.base_origem_temp = None
        self.limpar_selecao_visual()
        self.lbl_status.configure(text="Modo: Visualização", text_color="gray")

    def voltar(self):
        self.ativar_modo_visualizacao()
        self.app.mostrar_tela_inicial()

    def exportar_json(self):
        caminho = salvar_configuracao_interface(
            self.app.dados_simulacao,
            self.app.caminho_configuracao_atual,
        )
        self.app.caminho_configuracao_atual = caminho
        messagebox.showinfo("Sucesso", f"Configuração salva em:\n{caminho}")

    def salvar_configuracao_como(self):
        caminho_atual = Path(self.app.caminho_configuracao_atual)
        caminho = filedialog.asksaveasfilename(
            title="Salvar configuração",
            initialdir=str(caminho_atual.parent),
            initialfile=caminho_atual.name,
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            arquivo = salvar_configuracao_interface(self.app.dados_simulacao, caminho)
        except OSError as erro:
            messagebox.showerror("Erro", f"Não foi possível salvar a configuração:\n{erro}")
            return

        self.app.caminho_configuracao_atual = arquivo
        messagebox.showinfo("Sucesso", f"Configuração salva em:\n{arquivo}")

    def carregar_configuracao(self):
        caminho = filedialog.askopenfilename(
            title="Escolha uma configuração",
            initialdir=str(Path(self.app.caminho_configuracao_atual).parent),
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            configuracao = carregar_configuracao_interface(caminho)
        except (OSError, ValueError) as erro:
            messagebox.showerror("Erro", f"Não foi possível carregar a configuração:\n{erro}")
            return

        self.pausar_animacao()
        self.app.dados_simulacao = configuracao
        self.app.caminho_configuracao_atual = Path(caminho)
        self.limpar_simulacao_exibida()
        self.atualizar_lista_painel()
        self.redesenhar_mapa()
        self.lbl_status.configure(text=f"Configuração carregada: {Path(caminho).name}", text_color="#2ecc71")

    def escolher_pasta_saida(self):
        caminho = filedialog.askdirectory(
            title="Escolha a pasta de saída",
            initialdir=str(self.app.diretorio_saida),
        )
        if not caminho:
            return

        self.app.diretorio_saida = Path(caminho)
        self.atualizar_label_pasta_saida()
        self.lbl_status.configure(text="Pasta de saída atualizada", text_color="#2ecc71")

    def atualizar_label_pasta_saida(self):
        if not hasattr(self, "lbl_pasta_saida"):
            return

        caminho = Path(self.app.diretorio_saida)
        texto = str(caminho)
        if len(texto) > 34:
            texto = f"...{texto[-31:]}"
        self.lbl_pasta_saida.configure(text=f"Saída: {texto}")

    def alternar_animacao(self):
        if self.animacao_rodando:
            self.pausar_animacao()
            return

        if not self.nomes_interacoes and not self.executar_simulacao():
            return

        if self.tempo_animacao_atual >= self.tempo_total_animacao:
            self.mostrar_tempo_simulacao(0.0)

        self.iniciar_animacao()

    def executar_simulacao(self):
        self.pausar_animacao()
        try:
            configuracao = preparar_dados_interface(self.app.dados_simulacao)
            caminho_configuracao = salvar_configuracao_interface(
                configuracao,
                self.app.caminho_configuracao_atual,
            )
            self.app.caminho_configuracao_atual = caminho_configuracao
            execucao = executar_motor_simulacao(configuracao)
        except (KeyError, TypeError, ValueError) as erro:
            messagebox.showerror("Erro na Simulação", str(erro))
            return False

        pasta_saida = Path(self.app.diretorio_saida) / f"interface_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        salvar_resultado(pasta_saida, execucao.interacoes, execucao.resultado_final)

        self.interacoes_simulacao = execucao.interacoes
        self.resultado_final_simulacao = execucao.resultado_final
        self.nomes_interacoes = sorted(
            self.interacoes_simulacao,
            key=self.chave_ordenacao_interacao,
        )
        self.indice_interacao_atual = 0
        self.pasta_resultado_simulacao = pasta_saida
        self.montar_quadros_timeline()
        self.configurar_timeline_visual()

        self.mostrar_tempo_simulacao(0.0)
        self.atualizar_resumo_resultado(caminho_configuracao)
        return True

    def chave_ordenacao_interacao(self, nome_interacao):
        try:
            return int(nome_interacao.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            return 0

    def montar_quadros_timeline(self):
        if not self.resultado_final_simulacao:
            self.quadros_timeline = []
            self.tempo_total_animacao = 0.0
            return

        tempos = self.resultado_final_simulacao["tempos_interacoes"]
        self.quadros_timeline = [
            (nome, float(tempos.get(nome, 0.0)), self.interacoes_simulacao[nome])
            for nome in self.nomes_interacoes
        ]
        tempo_final = float(self.resultado_final_simulacao.get("tempo_total", 0.0))
        if self.quadros_timeline:
            tempo_final = max(tempo_final, self.quadros_timeline[-1][1])
        self.tempo_total_animacao = max(0.0, tempo_final)
        self.tempo_animacao_atual = 0.0

    def configurar_timeline_visual(self):
        limite = max(self.tempo_total_animacao, 1.0)
        self.atualizando_timeline = True
        self.timeline_slider.configure(from_=0, to=limite)
        self.timeline_slider.set(0)
        self.atualizando_timeline = False
        self.lbl_tempo_timeline.configure(
            text=f"t=0 / {self.formatar_tempo(self.tempo_total_animacao)}"
        )

    def iniciar_animacao(self):
        if not self.quadros_timeline:
            return

        if self.tempo_total_animacao <= 0:
            self.mostrar_tempo_simulacao(0.0)
            return

        self.animacao_rodando = True
        self.ultimo_tick_animacao = monotonic()
        self.btn_simular.configure(text="Pausar")
        self.lbl_status.configure(text="Simulação em execução", text_color="#7d3c98")
        self.animacao_after_id = self.parent.after(33, self.animar_timeline)

    def pausar_animacao(self):
        if self.animacao_after_id is not None:
            self.parent.after_cancel(self.animacao_after_id)
            self.animacao_after_id = None

        estava_rodando = self.animacao_rodando
        self.animacao_rodando = False
        if hasattr(self, "btn_simular"):
            self.btn_simular.configure(text="Simular")
        if estava_rodando and hasattr(self, "lbl_status"):
            self.lbl_status.configure(text="Simulação pausada", text_color="gray")

    def animar_timeline(self):
        if not self.animacao_rodando:
            return

        agora = monotonic()
        delta_real = max(0.0, agora - self.ultimo_tick_animacao)
        self.ultimo_tick_animacao = agora

        duracao_reproducao = max(4.0, min(12.0, len(self.quadros_timeline) * 1.5))
        passo = (self.tempo_total_animacao / duracao_reproducao) * delta_real
        proximo_tempo = self.tempo_animacao_atual + passo

        if proximo_tempo >= self.tempo_total_animacao:
            self.mostrar_tempo_simulacao(self.tempo_total_animacao)
            self.pausar_animacao()
            self.lbl_status.configure(text="Simulação concluída", text_color="#2ecc71")
            return

        self.mostrar_tempo_simulacao(proximo_tempo)
        self.animacao_after_id = self.parent.after(33, self.animar_timeline)

    def arrastar_timeline(self, valor):
        if self.atualizando_timeline:
            return

        self.pausar_animacao()
        self.mostrar_tempo_simulacao(float(valor), atualizar_slider=False)

    def interacao_anterior(self):
        if not self.quadros_timeline:
            return
        self.mostrar_interacao(self.indice_interacao_atual - 1)

    def proxima_interacao(self):
        if not self.quadros_timeline:
            return
        self.mostrar_interacao(self.indice_interacao_atual + 1)

    def mostrar_interacao(self, indice):
        if not self.quadros_timeline:
            return

        indice = max(0, min(indice, len(self.quadros_timeline) - 1))
        self.mostrar_tempo_simulacao(self.quadros_timeline[indice][1])

    def mostrar_tempo_simulacao(self, tempo, atualizar_slider=True):
        if not self.quadros_timeline:
            return

        tempo = max(0.0, min(float(tempo), self.tempo_total_animacao))
        self.tempo_animacao_atual = tempo

        indice_a, quadro_a, quadro_b, fracao = self.localizar_quadros_por_tempo(tempo)
        nome_a, _tempo_a, estado_a = quadro_a
        nome_b, _tempo_b, estado_b = quadro_b
        self.indice_interacao_atual = indice_a

        self.desenhar_estado_timeline(estado_a, estado_b, fracao)
        self.atualizar_label_interacao(nome_a, nome_b, fracao)
        if atualizar_slider:
            self.atualizando_timeline = True
            self.timeline_slider.set(tempo)
            self.atualizando_timeline = False

    def localizar_quadros_por_tempo(self, tempo):
        if tempo <= self.quadros_timeline[0][1]:
            primeiro = self.quadros_timeline[0]
            return 0, primeiro, primeiro, 0.0

        for indice in range(len(self.quadros_timeline) - 1):
            quadro_a = self.quadros_timeline[indice]
            quadro_b = self.quadros_timeline[indice + 1]
            tempo_a = quadro_a[1]
            tempo_b = quadro_b[1]
            if tempo <= tempo_b:
                duracao = max(tempo_b - tempo_a, 1e-9)
                fracao = max(0.0, min(1.0, (tempo - tempo_a) / duracao))
                return indice, quadro_a, quadro_b, fracao

        ultimo_indice = len(self.quadros_timeline) - 1
        ultimo = self.quadros_timeline[ultimo_indice]
        return ultimo_indice, ultimo, ultimo, 1.0

    def desenhar_estado_timeline(self, estado_a, estado_b, fracao):
        self.canvas.delete("simulacao")

        nomes_drones = list(estado_a)
        for nome_drone in estado_b:
            if nome_drone not in estado_a:
                nomes_drones.append(nome_drone)

        for nome_drone in nomes_drones:
            dados_a = estado_a.get(nome_drone) or estado_b[nome_drone]
            dados_b = estado_b.get(nome_drone) or dados_a
            posicao_a = dados_a["posicao_atual"]
            posicao_b = dados_b["posicao_atual"]
            posicao = [
                posicao_a[0] + (posicao_b[0] - posicao_a[0]) * fracao,
                posicao_a[1] + (posicao_b[1] - posicao_a[1]) * fracao,
            ]
            status = self.status_animado(dados_a["status"], dados_b["status"], fracao)
            px_x, px_y = self.km_para_pixels(posicao[0], posicao[1])
            cor = self.cor_status(status)
            raio_marcador = 6
            raio_drone = float(
                self.app.dados_simulacao["drones"]
                .get(nome_drone, {})
                .get("raio", 0)
            )
            if fracao > 0 and posicao_a != posicao_b:
                inicio_x, inicio_y = self.km_para_pixels(posicao_a[0], posicao_a[1])
                self.canvas.create_line(
                    inicio_x,
                    inicio_y,
                    px_x,
                    px_y,
                    fill=cor,
                    width=3,
                    tags=("simulacao",),
                )
            if raio_drone > 0:
                raio_x, raio_y = self.raio_km_para_pixels(raio_drone)
                raio_x = max(raio_x, raio_marcador + 7)
                raio_y = max(raio_y, raio_marcador + 7)
                self.canvas.create_oval(
                    px_x - raio_x,
                    px_y - raio_y,
                    px_x + raio_x,
                    px_y + raio_y,
                    outline=cor,
                    width=2,
                    tags=("simulacao",),
                )
                self.canvas.create_text(
                    px_x + raio_x + 16,
                    px_y,
                    text=f"r={self.formatar_tempo(raio_drone)}",
                    fill=cor,
                    font=("Arial", 9, "bold"),
                    tags=("simulacao",),
                )
            self.canvas.create_oval(
                px_x - raio_marcador,
                px_y - raio_marcador,
                px_x + raio_marcador,
                px_y + raio_marcador,
                fill=cor,
                outline="white",
                width=2,
                tags=("simulacao",),
            )
            self.canvas.create_text(
                px_x,
                px_y - 18,
                text=nome_drone,
                fill="white",
                font=("Arial", 10, "bold"),
                tags=("simulacao",),
            )
            self.canvas.create_text(
                px_x,
                px_y + 18,
                text=status,
                fill=cor,
                font=("Arial", 9, "bold"),
                tags=("simulacao",),
            )

    def status_animado(self, status_a, status_b, fracao):
        if fracao <= 0.001:
            return status_a
        if fracao >= 0.999:
            return status_b
        if status_a == "entregou" or status_a == "nao concluiu" or status_a.startswith("bateu"):
            return status_a
        return "foi para"

    def cor_status(self, status):
        if status == "entregou":
            return "#2ecc71"
        if status.startswith("bateu"):
            return "#e74c3c"
        if status == "nao concluiu":
            return "#f39c12"
        return "#f1c40f"

    def formatar_tempo(self, tempo):
        tempo = float(tempo)
        if abs(tempo - round(tempo)) < 1e-9:
            return str(int(round(tempo)))
        return f"{tempo:.2f}".rstrip("0").rstrip(".")

    def atualizar_label_interacao(self, nome_a=None, nome_b=None, fracao=0.0):
        if not self.quadros_timeline or not self.resultado_final_simulacao:
            self.lbl_interacao.configure(text="Sem simulação")
            self.lbl_tempo_timeline.configure(text="t=0 / 0")
            return

        eventos = self.resultado_final_simulacao["eventos_interacoes"]
        nome_evento = nome_b if fracao >= 0.999 else nome_a
        eventos_texto = ", ".join(eventos.get(nome_evento, [])) if nome_evento else ""

        if nome_a and nome_b and nome_a != nome_b and fracao < 0.999:
            trecho = f"{nome_a} -> {nome_b}"
        else:
            trecho = nome_evento or "Sem simulação"

        texto = trecho
        if eventos_texto:
            texto = f"{texto}\n{eventos_texto}"

        self.lbl_tempo_timeline.configure(
            text=(
                f"t={self.formatar_tempo(self.tempo_animacao_atual)} / "
                f"{self.formatar_tempo(self.tempo_total_animacao)}"
            )
        )
        self.lbl_interacao.configure(text=texto)

    def atualizar_resumo_resultado(self, caminho_configuracao):
        if not self.resultado_final_simulacao:
            return

        resultado = self.resultado_final_simulacao
        linhas = [
            "Resumo final",
            f"Interações: {resultado['qtd_interacoes']}",
            f"Tempo total: {resultado['tempo_total']}",
            f"Entregues: {resultado['quantidade_ok']}",
            f"Colisões: {resultado['quantidade_bateu']}",
            f"Não concluíram: {resultado['quantidade_nao_concluiu']}",
            f"Sucesso: {resultado['taxa_sucesso']}",
            f"Fracasso: {resultado['taxa_fracasso']}",
            f"Distância total: {resultado['distancia_total_percorrida']}",
            f"Config: {caminho_configuracao}",
            f"Saída: {self.pasta_resultado_simulacao}",
        ]

        avisos = resultado.get("avisos_configuracao", [])
        if avisos:
            linhas.append("")
            linhas.append("Avisos:")
            linhas.extend(f"- {aviso}" for aviso in avisos)

        self.caixa_resultado.configure(state="normal")
        self.caixa_resultado.delete("1.0", "end")
        self.caixa_resultado.insert("1.0", "\n".join(linhas))
        self.caixa_resultado.configure(state="disabled")

    def limpar_simulacao_exibida(self):
        self.pausar_animacao()
        self.interacoes_simulacao = {}
        self.resultado_final_simulacao = None
        self.nomes_interacoes = []
        self.quadros_timeline = []
        self.indice_interacao_atual = 0
        self.pasta_resultado_simulacao = None
        self.tempo_animacao_atual = 0.0
        self.tempo_total_animacao = 0.0
        self.canvas.delete("simulacao")

        if hasattr(self, "lbl_interacao"):
            self.lbl_interacao.configure(text="Sem simulação")
        if hasattr(self, "lbl_tempo_timeline"):
            self.lbl_tempo_timeline.configure(text="t=0 / 0")
        if hasattr(self, "timeline_slider"):
            self.atualizando_timeline = True
            self.timeline_slider.configure(from_=0, to=1)
            self.timeline_slider.set(0)
            self.atualizando_timeline = False
        if hasattr(self, "caixa_resultado"):
            self.caixa_resultado.configure(state="normal")
            self.caixa_resultado.delete("1.0", "end")
            self.caixa_resultado.insert("1.0", "Resultado da simulação aparecerá aqui.")
            self.caixa_resultado.configure(state="disabled")

    # ================== FORMULÁRIOS CONSOLIDADOS (CRIAR/EDITAR) ==================
    def abrir_formulario_base(self, km_x, km_y, editando_nome=None):
        JanelaFormularioBase(self, km_x, km_y, editando_nome)

    def salvar_base(self, nome, km_x, km_y, raio, editando_nome):
        self.limpar_simulacao_exibida()
        # Salva os dados lógicos em KM perfeitamente!
        self.app.dados_simulacao["Pontos"][nome] = {"x": km_x, "y": km_y, "r": raio}
        
        if editando_nome:
            id_oval_antigo = self.canvas_items["bases"][nome]["oval"]
            id_texto_antigo = self.canvas_items["bases"][nome]["texto"]
            self.canvas.delete(id_oval_antigo)
            self.canvas.delete(id_texto_antigo)

        # Converte para pixels apenas para desenhar na tela do usuário
        px_x, px_y = self.km_para_pixels(km_x, km_y)
        raio_visual = 10 
        id_oval = self.canvas.create_oval(px_x - raio_visual, px_y - raio_visual, px_x + raio_visual, px_y + raio_visual, fill="#2ecc71", outline="white")
        id_texto = self.canvas.create_text(px_x, px_y + 20, text=nome, fill="white", font=("Arial", 12, "bold"))
        self.canvas_items["bases"][nome] = {"oval": id_oval, "texto": id_texto}
        
        # Atualiza rotas de drones grudadinhos
        for nome_drone, dados_drone in self.app.dados_simulacao["drones"].items():
            origem = dados_drone["posicao_inicial"]
            destino = dados_drone["posicao_destino"]
            
            if origem == nome or destino == nome:
                p1_km = self.app.dados_simulacao["Pontos"][origem]
                p2_km = self.app.dados_simulacao["Pontos"][destino]
                
                p1_px_x, p1_px_y = self.km_para_pixels(p1_km["x"], p1_km["y"])
                p2_px_x, p2_px_y = self.km_para_pixels(p2_km["x"], p2_km["y"])
                
                id_linha = self.canvas_items["drones"][nome_drone]["linha"]
                id_texto_drone = self.canvas_items["drones"][nome_drone]["texto"]
                
                self.canvas.coords(id_linha, p1_px_x, p1_px_y, p2_px_x, p2_px_y)
                meio_x, meio_y = (p1_px_x + p2_px_x) / 2, (p1_px_y + p2_px_y) / 2
                self.canvas.coords(id_texto_drone, meio_x, meio_y - 10)
        
        self.atualizar_lista_painel()
        self.ativar_modo_visualizacao()

    def deletar_base(self, nome):
        for drone, dados in self.app.dados_simulacao["drones"].items():
            if dados["posicao_inicial"] == nome or dados["posicao_destino"] == nome:
                messagebox.showerror("Ação Negada", f"Não é possível apagar a base '{nome}' porque o '{drone}' está usando ela.")
                return False

        self.limpar_simulacao_exibida()
        self.canvas.delete(self.canvas_items["bases"][nome]["oval"])
        self.canvas.delete(self.canvas_items["bases"][nome]["texto"])
        del self.app.dados_simulacao["Pontos"][nome]
        del self.canvas_items["bases"][nome]

        self.atualizar_lista_painel()
        self.ativar_modo_visualizacao()
        return True

    def abrir_formulario_drone(self, origem, destino, editando_nome=None):
        JanelaFormularioDrone(self, origem, destino, editando_nome)

    def salvar_drone(self, nome, origem, destino, velocidade, raio, editando_nome):
        self.limpar_simulacao_exibida()
        self.app.dados_simulacao["drones"][nome] = {
            "posicao_inicial": origem,
            "posicao_destino": destino,
            "raio": raio,
            "velocidade": velocidade
        }
        self.app.dados_simulacao["numero_drones"] = len(self.app.dados_simulacao["drones"])

        if not editando_nome:
            p1_km = self.app.dados_simulacao["Pontos"][origem]
            p2_km = self.app.dados_simulacao["Pontos"][destino]
            
            p1_px_x, p1_px_y = self.km_para_pixels(p1_km["x"], p1_km["y"])
            p2_px_x, p2_px_y = self.km_para_pixels(p2_km["x"], p2_km["y"])
            
            id_linha = self.canvas.create_line(p1_px_x, p1_px_y, p2_px_x, p2_px_y, arrow="last", fill="#1f6aa5", width=2, dash=(4, 4))
            meio_x, meio_y = (p1_px_x + p2_px_x) / 2, (p1_px_y + p2_px_y) / 2
            id_texto = self.canvas.create_text(meio_x, meio_y - 10, text=nome, fill="#1f6aa5", font=("Arial", 10, "bold"))
            self.canvas_items["drones"][nome] = {"linha": id_linha, "texto": id_texto}

        self.atualizar_lista_painel()
        self.ativar_modo_visualizacao()
        
    def deletar_drone(self, nome):
        self.limpar_simulacao_exibida()
        self.canvas.delete(self.canvas_items["drones"][nome]["linha"])
        self.canvas.delete(self.canvas_items["drones"][nome]["texto"])
        del self.app.dados_simulacao["drones"][nome]
        del self.canvas_items["drones"][nome]
        self.app.dados_simulacao["numero_drones"] = len(self.app.dados_simulacao["drones"])
        self.atualizar_lista_painel()
        self.ativar_modo_visualizacao()


# ================== CLASSES DAS JANELAS MODAIS ==================

def ativar_modal_quando_visivel(janela):
    def ativar():
        if not janela.winfo_exists():
            return

        if not janela.winfo_viewable():
            janela.after(50, ativar)
            return

        try:
            janela.lift()
            janela.focus_force()
            janela.grab_set()
        except TclError:
            janela.after(50, ativar)

    janela.after_idle(ativar)


class JanelaFormularioBase(ctk.CTkToplevel):
    def __init__(self, tela_mapa, km_x, km_y, editando_nome=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.editando_nome = editando_nome

        self.title("Configuração de Base")
        self.geometry("320x350")
        self.attributes("-topmost", True) 

        lbl_titulo = ctk.CTkLabel(self, text="Dados da Base", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)

        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="Nome (ex: Base 1)")
        self.entrada_nome.pack(pady=5, padx=20, fill="x")

        self.entrada_x = ctk.CTkEntry(self, placeholder_text="Coordenada X (km)")
        self.entrada_x.pack(pady=5, padx=20, fill="x")
        self.entrada_x.insert(0, str(km_x)) 

        self.entrada_y = ctk.CTkEntry(self, placeholder_text="Coordenada Y (km)")
        self.entrada_y.pack(pady=5, padx=20, fill="x")
        self.entrada_y.insert(0, str(km_y))

        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="Raio de Chegada (km)")
        self.entrada_raio.pack(pady=5, padx=20, fill="x")

        if editando_nome:
            dados_atuais = self.tela_mapa.app.dados_simulacao["Pontos"][editando_nome]
            self.entrada_nome.insert(0, editando_nome)
            self.entrada_nome.configure(state="disabled") 
            self.entrada_x.delete(0, 'end')
            self.entrada_x.insert(0, str(dados_atuais["x"]))
            self.entrada_y.delete(0, 'end')
            self.entrada_y.insert(0, str(dados_atuais["y"]))
            self.entrada_raio.insert(0, str(dados_atuais["r"]))

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=15)

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar", command=self.salvar, width=100)
        btn_salvar.pack(side="left", padx=10)

        if editando_nome:
            btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar", fg_color="#c0392b", hover_color="#922b21", command=self.deletar, width=100)
            btn_deletar.pack(side="right", padx=10)

        ativar_modal_quando_visivel(self)

    def salvar(self):
        nome = self.entrada_nome.get()
        try:
            val_x = float(self.entrada_x.get())
            val_y = float(self.entrada_y.get())
            val_raio = float(self.entrada_raio.get())
            
            # Validação: Não deixa colocar coordenadas em km maiores que o tamanho do ambiente
            max_largura, max_altura = self.tela_mapa.app.dados_simulacao["tamanho_ambiente"]
            if val_x < 0 or val_x > max_largura or val_y < 0 or val_y > max_altura:
                messagebox.showerror("Erro", f"As coordenadas devem estar dentro do mapa lógico (0 a {max_largura} em X, 0 a {max_altura} em Y).")
                self.attributes("-topmost", True)
                return
        except ValueError:
            messagebox.showerror("Erro", "Valores devem ser numéricos.")
            self.attributes("-topmost", True)
            return

        if not nome:
            messagebox.showerror("Erro", "O nome não pode ficar vazio.")
            self.attributes("-topmost", True)
            return

        self.tela_mapa.salvar_base(nome, val_x, val_y, val_raio, self.editando_nome)
        self.destroy()

    def deletar(self):
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja apagar a base '{self.editando_nome}'?"):
            sucesso = self.tela_mapa.deletar_base(self.editando_nome)
            if sucesso:
                self.destroy()
            else:
                self.attributes("-topmost", True)


class JanelaFormularioDrone(ctk.CTkToplevel):
    def __init__(self, tela_mapa, origen, destino, editando_nome=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.origem = origen
        self.destino = destino
        self.editando_nome = editando_nome

        self.title("Configuração do Drone")
        self.geometry("320x300")
        self.attributes("-topmost", True)

        lbl_titulo = ctk.CTkLabel(self, text="Dados do Drone", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)

        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="Identificador (ex: Drone 1)")
        self.entrada_nome.pack(pady=10, padx=20, fill="x")

        self.entrada_vel = ctk.CTkEntry(self, placeholder_text="Velocidade (km/h)")
        self.entrada_vel.pack(pady=10, padx=20, fill="x")

        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="Raio do Drone (Colisão)")
        self.entrada_raio.pack(pady=10, padx=20, fill="x")

        if editando_nome:
            dados_atuais = self.tela_mapa.app.dados_simulacao["drones"][editando_nome]
            self.origem = dados_atuais["posicao_inicial"]
            self.destino = dados_atuais["posicao_destino"]
            
            self.entrada_nome.insert(0, editando_nome)
            self.entrada_nome.configure(state="disabled")
            self.entrada_vel.insert(0, str(dados_atuais["velocidade"]))
            self.entrada_raio.insert(0, str(dados_atuais["raio"]))

        lbl_info = ctk.CTkLabel(self, text=f"Rota: {self.origem} -> {self.destino}", text_color="gray")
        lbl_info.pack(pady=5)

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar", command=self.salvar, width=100)
        btn_salvar.pack(side="left", padx=10)

        if editando_nome:
            btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar", fg_color="#c0392b", hover_color="#922b21", command=self.deletar, width=100)
            btn_deletar.pack(side="right", padx=10)

        ativar_modal_quando_visivel(self)

    def salvar(self):
        nome = self.entrada_nome.get()
        try:
            vel = float(self.entrada_vel.get())
            raio = float(self.entrada_raio.get())
        except ValueError:
            messagebox.showerror("Erro", "Velocidade e Raio devem ser numéricos!")
            self.attributes("-topmost", True)
            return

        if not nome:
            return

        self.tela_mapa.salvar_drone(nome, self.origem, self.destino, vel, raio, self.editando_nome)
        self.destroy()

    def deletar(self):
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja apagar o '{self.editando_nome}'?"):
            self.tela_mapa.deletar_drone(self.editando_nome)
            self.destroy()
