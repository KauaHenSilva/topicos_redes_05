import math
import customtkinter as ctk
from tkinter import Canvas, messagebox

class TelaMapa:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.modo_atual = None  
        self.base_origem_temp = None  
        self.id_circulo_selecao = None 
        
        self.canvas_items = {"bases": {}, "drones": {}}
        self.item_selecionado = {"tipo": None, "nome": None}
        
        self.construir_tela()

    def construir_tela(self):
        self.painel_lateral = ctk.CTkFrame(self.parent, width=280)
        self.painel_lateral.pack(side="right", fill="y", padx=10, pady=10)

        lbl_ferramentas = ctk.CTkLabel(self.painel_lateral, text="Ferramentas", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_ferramentas.pack(pady=(15, 10))

        self.btn_modo_base = ctk.CTkButton(self.painel_lateral, text="📍 Criar Base (Ponto)", fg_color="green", command=self.ativar_modo_base)
        self.btn_modo_base.pack(pady=5, padx=20)

        self.btn_modo_drone = ctk.CTkButton(self.painel_lateral, text="🚁 Criar Drone", command=self.ativar_modo_drone)
        self.btn_modo_drone.pack(pady=5, padx=20)

        self.lbl_status = ctk.CTkLabel(self.painel_lateral, text="Modo: Visualização", text_color="gray")
        self.lbl_status.pack(pady=10)

        lbl_lista = ctk.CTkLabel(self.painel_lateral, text="Elementos Criados", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_lista.pack(pady=(10, 5))
        
        self.scroll_lista = ctk.CTkScrollableFrame(self.painel_lateral, height=200)
        self.scroll_lista.pack(fill="both", expand=True, padx=10, pady=5)

        self.btn_voltar = ctk.CTkButton(self.painel_lateral, text="⬅ Voltar à Configuração", fg_color="#555555", hover_color="#333333", command=self.voltar)
        self.btn_voltar.pack(side="bottom", pady=(10, 15), padx=20)

        self.btn_exportar = ctk.CTkButton(self.painel_lateral, text="💾 Exportar JSON", fg_color="orange", hover_color="#cc7000", command=self.exportar_json)
        self.btn_exportar.pack(side="bottom", pady=5, padx=20)

        self.frame_mapa = ctk.CTkFrame(self.parent)
        self.frame_mapa.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.canvas = Canvas(self.frame_mapa, bg="#2b2b2b", highlightthickness=1, highlightbackground="#555555")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.registrar_clique)

        self.canvas.bind("<Configure>", self.redesenhar_mapa)

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

    # ================== LÓGICA DE LISTA E SELEÇÃO ==================
    def atualizar_lista_painel(self):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        for nome_base in self.app.dados_simulacao["Pontos"]:
            btn = ctk.CTkButton(self.scroll_lista, text=f"📍 {nome_base}", anchor="w", fg_color="transparent", 
                                text_color="white", hover_color="#444444", 
                                command=lambda n=nome_base: self.clicar_item_lista("base", n))
            btn.pack(fill="x", pady=2)

        for nome_drone in self.app.dados_simulacao["drones"]:
            btn = ctk.CTkButton(self.scroll_lista, text=f"🚁 {nome_drone}", anchor="w", fg_color="transparent", 
                                text_color="white", hover_color="#444444", 
                                command=lambda n=nome_drone: self.clicar_item_lista("drone", n))
            btn.pack(fill="x", pady=2)

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
        print("JSON FINAL COMPLETO:\n", self.app.dados_simulacao)
        messagebox.showinfo("Sucesso", "Olhe o console para ver o JSON final em Quilômetros!")

    # ================== FORMULÁRIOS CONSOLIDADOS (CRIAR/EDITAR) ==================
    def abrir_formulario_base(self, km_x, km_y, editando_nome=None):
        JanelaFormularioBase(self, km_x, km_y, editando_nome)

    def salvar_base(self, nome, km_x, km_y, raio, editando_nome):
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
        self.canvas.delete(self.canvas_items["drones"][nome]["linha"])
        self.canvas.delete(self.canvas_items["drones"][nome]["texto"])
        del self.app.dados_simulacao["drones"][nome]
        del self.canvas_items["drones"][nome]
        self.app.dados_simulacao["numero_drones"] = len(self.app.dados_simulacao["drones"])
        self.atualizar_lista_painel()
        self.ativar_modo_visualizacao()


# ================== CLASSES DAS JANELAS MODAIS ==================

class JanelaFormularioBase(ctk.CTkToplevel):
    def __init__(self, tela_mapa, km_x, km_y, editando_nome=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.editando_nome = editando_nome

        self.title("Configuração de Base")
        self.geometry("320x350")
        self.attributes("-topmost", True) 
        self.grab_set() 

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
        self.grab_set() 

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

        lbl_info = ctk.CTkLabel(self, text=f"Rota: {self.origem} ➔ {self.destino}", text_color="gray")
        lbl_info.pack(pady=5)

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar", command=self.salvar, width=100)
        btn_salvar.pack(side="left", padx=10)

        if editando_nome:
            btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar", fg_color="#c0392b", hover_color="#922b21", command=self.deletar, width=100)
            btn_deletar.pack(side="right", padx=10)

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