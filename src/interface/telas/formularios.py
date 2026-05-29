import math
import customtkinter as ctk
from tkinter import messagebox, TclError


def ativar_modal_quando_visivel(janela):
    def activar():
        if not janela.winfo_exists():
            return

        if not janela.winfo_viewable():
            janela.after(50, activar)
            return

        try:
            janela.lift()
            janela.focus_force()
            janela.grab_set()
        except TclError:
            janela.after(50, activar)

    janela.after_idle(activar)


class JanelaFormularioBase(ctk.CTkToplevel):
    def __init__(self, tela_mapa, km_x, km_y, editando_nome=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.editando_nome = editando_nome

        self.title("Configuração de Base")
        self.geometry("350x450")
        self.attributes("-topmost", True) 

        lbl_titulo = ctk.CTkLabel(self, text="Dados da Base", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        lbl_nome = ctk.CTkLabel(self, text="Nome da Base:", text_color="gray", anchor="w")
        lbl_nome.pack(padx=20, fill="x")
        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="ex: Base 1")
        self.entrada_nome.pack(pady=(0, 10), padx=20, fill="x")

        lbl_x = ctk.CTkLabel(self, text="Coordenada X (km):", text_color="gray", anchor="w")
        lbl_x.pack(padx=20, fill="x")
        self.entrada_x = ctk.CTkEntry(self, placeholder_text="ex: 100.0")
        self.entrada_x.pack(pady=(0, 10), padx=20, fill="x")
        self.entrada_x.insert(0, str(km_x)) 

        lbl_y = ctk.CTkLabel(self, text="Coordenada Y (km):", text_color="gray", anchor="w")
        lbl_y.pack(padx=20, fill="x")
        self.entrada_y = ctk.CTkEntry(self, placeholder_text="ex: 150.0")
        self.entrada_y.pack(pady=(0, 10), padx=20, fill="x")
        self.entrada_y.insert(0, str(km_y))

        lbl_raio = ctk.CTkLabel(self, text="Raio de Chegada / Tamanho (km):", text_color="gray", anchor="w")
        lbl_raio.pack(padx=20, fill="x")
        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="ex: 5.0")
        self.entrada_raio.pack(pady=(0, 15), padx=20, fill="x")

        if editando_nome:
            dados_atuais = self.tela_mapa.app.dados_simulacao["Pontos"][editando_nome]
            self.entrada_nome.insert(0, editando_nome)
            self.entrada_x.delete(0, 'end')
            self.entrada_x.insert(0, str(dados_atuais["x"]))
            self.entrada_y.delete(0, 'end')
            self.entrada_y.insert(0, str(dados_atuais["y"]))
            self.entrada_raio.insert(0, str(dados_atuais.get("r", 1.0)))

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar", command=self.salvar, width=100)
        btn_salvar.pack(side="left", padx=10)

        if editando_nome:
            btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar", fg_color="#c0392b", hover_color="#922b21", command=self.deletar, width=100)
            btn_deletar.pack(side="right", padx=10)

        ativar_modal_quando_visivel(self)

    def salvar(self):
        nome = self.entrada_nome.get().strip()

        if not nome:
            messagebox.showerror("Erro", "O nome não pode ficar vazio.")
            self.attributes("-topmost", True)
            return

        if nome in self.tela_mapa.app.dados_simulacao.get("Pontos", {}):
            if self.editando_nome != nome:
                messagebox.showerror("Erro", f"Já existe uma Base chamada '{nome}'!")
                self.attributes("-topmost", True)
                return

        if nome in self.tela_mapa.app.dados_simulacao.get("drones", {}):
            if self.editando_nome != nome:
                messagebox.showerror("Erro", f"Já existe um Drone chamado '{nome}'!")
                self.attributes("-topmost", True)
                return

        try:
            val_x = float(self.entrada_x.get())
            val_y = float(self.entrada_y.get())
            val_raio = float(self.entrada_raio.get())
            
            max_largura, max_altura = self.tela_mapa.app.dados_simulacao["tamanho_ambiente"]
            if val_x < 0 or val_x > max_largura or val_y < 0 or val_y > max_altura:
                messagebox.showerror("Erro", f"As coordenadas devem estar dentro do mapa (0 a {max_largura} em X, 0 a {max_altura} em Y).")
                self.attributes("-topmost", True)
                return
        except ValueError:
            messagebox.showerror("Erro", "Valores devem ser numéricos (use ponto para decimais).")
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
    def __init__(self, tela_mapa, origem, destino, editando_nome=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.origem = origem
        
        # Previne erro caso destino chegue como None a partir da lista
        self.destinos = destino if isinstance(destino, list) else ([destino] if destino else [])
        self.editando_nome = editando_nome

        self.title("Configuração do Drone")
        self.geometry("400x700") 
        self.attributes("-topmost", True)

        lbl_titulo = ctk.CTkLabel(self, text="Dados do Drone", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        # --- NOME ---
        lbl_nome = ctk.CTkLabel(self, text="Identificador do Drone:", text_color="gray", anchor="w")
        lbl_nome.pack(padx=20, fill="x")
        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="ex: Drone 1")
        self.entrada_nome.pack(pady=(0, 10), padx=20, fill="x")

        # --- VELOCIDADE ---
        lbl_vel = ctk.CTkLabel(self, text="Velocidade Média (km/h):", text_color="gray", anchor="w")
        lbl_vel.pack(padx=20, fill="x")
        self.entrada_vel = ctk.CTkEntry(self, placeholder_text="ex: 60.0")
        self.entrada_vel.pack(pady=(0, 10), padx=20, fill="x")

        # --- RAIO ---
        lbl_raio = ctk.CTkLabel(self, text="Raio de Colisão (km):", text_color="gray", anchor="w")
        lbl_raio.pack(padx=20, fill="x")
        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="ex: 2.0")
        self.entrada_raio.pack(pady=(0, 10), padx=20, fill="x")

        # Variável para rastrear a base de entrega previamente salva
        base_entrega_salva = self.destinos[-1] if self.destinos else None

        if editando_nome:
            dados_atuais = self.tela_mapa.app.dados_simulacao["drones"][editando_nome]
            
            # --- CORREÇÃO CRUCIAL AQUI ---
            # Se origem for None (abriu pela lista), carregamos a rota velha do JSON.
            # Se origem NÃO for None (veio do botão de Confirmar Rota), mantemos a nova!
            if self.origem is None:
                self.origem = dados_atuais["posicao_inicial"]
                self.destinos = dados_atuais.get("rota", [dados_atuais.get("posicao_destino")])
            
            base_entrega_salva = dados_atuais.get("base_entrega", self.destinos[-1] if self.destinos else None)
            
            # Se a base salva não faz mais parte da nova rota redesenhada, reseta para a última
            if base_entrega_salva not in self.destinos and self.destinos:
                base_entrega_salva = self.destinos[-1]
            
            self.entrada_nome.insert(0, editando_nome)
            self.entrada_nome.configure(state="disabled")
            self.entrada_vel.insert(0, str(dados_atuais["velocidade"]))
            self.entrada_raio.insert(0, str(dados_atuais["raio"]))

        # --- BASE DE ENTREGA (Opção de Seleção) ---
        lbl_entrega = ctk.CTkLabel(self, text="Base de Entrega (Destino Principal):", text_color="gray", anchor="w")
        lbl_entrega.pack(padx=20, fill="x")
        
        self.var_base_entrega = ctk.StringVar(value=base_entrega_salva)
        self.combo_entrega = ctk.CTkOptionMenu(
            self,
            variable=self.var_base_entrega,
            values=self.destinos,
            fg_color="#34495e", button_color="#2c3e50"
        )
        self.combo_entrega.pack(padx=20, fill="x", pady=(0, 10))

        # --- CÁLCULO E EXIBIÇÃO DAS DISTÂNCIAS ---
        caminho_completo = [self.origem] + self.destinos
        distancia_total = 0.0
        textos_trechos = []
        
        for i in range(len(caminho_completo) - 1):
            p1_nome = caminho_completo[i]
            p2_nome = caminho_completo[i+1]
            
            p1 = self.tela_mapa.app.dados_simulacao["Pontos"][p1_nome]
            p2 = self.tela_mapa.app.dados_simulacao["Pontos"][p2_nome]
            
            dist = math.hypot(p2["x"] - p1["x"], p2["y"] - p1["y"])
            distancia_total += dist
            textos_trechos.append(f"• {p1_nome} ➔ {p2_nome}: {dist:.2f} km")

        lbl_rota_titulo = ctk.CTkLabel(self, text="Distâncias por Trecho:", text_color="#2ecc71", font=("Arial", 12, "bold"))
        lbl_rota_titulo.pack(pady=(5, 0))

        frame_rotas = ctk.CTkScrollableFrame(self, height=80, fg_color="#2b2b2b")
        frame_rotas.pack(padx=20, fill="x", pady=5)

        for trecho in textos_trechos:
            lbl_t = ctk.CTkLabel(frame_rotas, text=trecho, font=("Arial", 11))
            lbl_t.pack(anchor="w")

        lbl_dist_total = ctk.CTkLabel(self, text=f"Distância Total: {distancia_total:.2f} km", text_color="#3498db", font=("Arial", 14, "bold"))
        lbl_dist_total.pack(pady=(5, 10))

        # --- CONFIGURAÇÃO E EMPILHAMENTO DOS BOTÕES INFERIORES ---
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(side="bottom", pady=(0, 20)) 

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar", command=self.salvar, width=100)
        btn_salvar.pack(side="left", padx=10)

        if editando_nome:
            btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar", fg_color="#c0392b", hover_color="#922b21", command=self.deletar, width=100)
            btn_deletar.pack(side="right", padx=10)

        if editando_nome:
            btn_redesenhar = ctk.CTkButton(
                self, text="Redesenhar Rota no Mapa", 
                fg_color="#f39c12", hover_color="#d35400", text_color="white",
                command=self.redesenhar_rota
            )
            btn_redesenhar.pack(side="bottom", pady=(0, 15))

        try:
            ativar_modal_quando_visivel(self)
        except NameError:
            self.after(200, self.grab_set)

    def redesenhar_rota(self):
        self.tela_mapa.ativar_modo_drone(editando_nome=self.editando_nome)
        self.destroy()

    def salvar(self):
        nome = self.entrada_nome.get()
        if not nome:
            messagebox.showerror("Erro", "O identificador não pode ficar vazio.")
            self.attributes("-topmost", True)
            return

        nome_em_uso_drones = (not self.editando_nome and nome in self.tela_mapa.app.dados_simulacao.get("drones", {})) or \
                             (self.editando_nome and nome != self.editando_nome and nome in self.tela_mapa.app.dados_simulacao.get("drones", {}))
                             
        nome_em_uso_bases = nome in self.tela_mapa.app.dados_simulacao.get("Pontos", {})

        if nome_em_uso_drones or nome_em_uso_bases:
            messagebox.showerror("Erro", "Já existe um elemento (Base ou Drone) com esse nome!")
            self.attributes("-topmost", True)
            return

        try:
            vel = float(self.entrada_vel.get())
            raio = float(self.entrada_raio.get())
        except ValueError:
            messagebox.showerror("Erro", "Velocidade e Raio devem ser numéricos!")
            self.attributes("-topmost", True)
            return
            
        base_entrega = self.var_base_entrega.get()
        self.tela_mapa.salvar_drone(nome, self.origem, self.destinos, vel, raio, self.editando_nome, base_entrega=base_entrega)
        self.destroy()

    def deletar(self):
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja apagar o '{self.editando_nome}'?"):
            self.tela_mapa.deletar_drone(self.editando_nome)
            self.destroy()


class JanelaFormularioModeloDrone(ctk.CTkToplevel):
    def __init__(self, tela_mapa, editando_modelo=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.editando_modelo = editando_modelo

        titulo = "Editar Modelo" if editando_modelo else "Criar Modelo"
        self.title(titulo)
        self.geometry("350x380")
        self.attributes("-topmost", True)

        lbl_titulo = ctk.CTkLabel(self, text=titulo, font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        lbl_nome = ctk.CTkLabel(self, text="Nome do Modelo:", text_color="gray", anchor="w")
        lbl_nome.pack(padx=20, fill="x")
        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="ex: Hopstein")
        self.entrada_nome.pack(pady=(0, 10), padx=20, fill="x")

        lbl_vel = ctk.CTkLabel(self, text="Velocidade Média (km/h):", text_color="gray", anchor="w")
        lbl_vel.pack(padx=20, fill="x")
        self.entrada_vel = ctk.CTkEntry(self, placeholder_text="ex: 60.0")
        self.entrada_vel.pack(pady=(0, 10), padx=20, fill="x")

        lbl_raio = ctk.CTkLabel(self, text="Raio de Colisão (km):", text_color="gray", anchor="w")
        lbl_raio.pack(padx=20, fill="x")
        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="ex: 2.0")
        self.entrada_raio.pack(pady=(0, 15), padx=20, fill="x")

        if self.editando_modelo:
            dados = self.tela_mapa.modelos_drones[self.editando_modelo]
            self.entrada_nome.insert(0, self.editando_modelo)
            self.entrada_vel.insert(0, str(dados["velocidade"]))
            self.entrada_raio.insert(0, str(dados["raio"]))

        btn_salvar = ctk.CTkButton(self, text="Salvar Modelo", command=self.salvar, width=150)
        btn_salvar.pack(pady=15)

        ativar_modal_quando_visivel(self)

    def salvar(self):
        nome = self.entrada_nome.get().strip()
        try:
            vel = float(self.entrada_vel.get())
            raio = float(self.entrada_raio.get())
        except ValueError:
            messagebox.showerror("Erro", "Velocidade e Raio devem ser numéricos!")
            self.attributes("-topmost", True)
            return

        if not nome:
            messagebox.showerror("Erro", "O modelo precisa de um nome!")
            self.attributes("-topmost", True)
            return

        if self.editando_modelo:
            if nome != self.editando_modelo and (nome == "Personalizado" or nome in self.tela_mapa.modelos_drones):
                messagebox.showerror("Erro", "Nome de modelo inválido ou já existente.")
                self.attributes("-topmost", True)
                return
            self.tela_mapa.atualizar_modelo_drone(self.editando_modelo, nome, vel, raio)
        else:
            if nome == "Personalizado" or nome in self.tela_mapa.modelos_drones:
                messagebox.showerror("Erro", "Nome de modelo inválido ou já existente.")
                self.attributes("-topmost", True)
                return
            self.tela_mapa.adicionar_modelo_drone(nome, vel, raio)
            
        self.destroy()

class JanelaFormularioModeloBase(ctk.CTkToplevel):
    def __init__(self, tela_mapa, editando_modelo=None):
        super().__init__()
        self.tela_mapa = tela_mapa
        self.editando_modelo = editando_modelo

        titulo = "Editar Modelo Base" if editando_modelo else "Criar Modelo Base"
        self.title(titulo)
        self.geometry("350x280")
        self.attributes("-topmost", True)

        lbl_titulo = ctk.CTkLabel(self, text=titulo, font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        lbl_nome = ctk.CTkLabel(self, text="Nome do Modelo de Base:", text_color="gray", anchor="w")
        lbl_nome.pack(padx=20, fill="x")
        self.entrada_nome = ctk.CTkEntry(self, placeholder_text="ex: Torre Principal")
        self.entrada_nome.pack(pady=(0, 10), padx=20, fill="x")

        lbl_raio = ctk.CTkLabel(self, text="Raio de Colisão (km):", text_color="gray", anchor="w")
        lbl_raio.pack(padx=20, fill="x")
        self.entrada_raio = ctk.CTkEntry(self, placeholder_text="ex: 5.0")
        self.entrada_raio.pack(pady=(0, 15), padx=20, fill="x")

        if self.editando_modelo:
            dados = self.tela_mapa.modelos_bases[self.editando_modelo]
            self.entrada_nome.insert(0, self.editando_modelo)
            self.entrada_raio.insert(0, str(dados["raio"]))

        btn_salvar = ctk.CTkButton(self, text="Salvar Modelo", command=self.salvar, width=150)
        btn_salvar.pack(pady=15)

        ativar_modal_quando_visivel(self)

    def salvar(self):
        nome = self.entrada_nome.get().strip()
        try:
            raio = float(self.entrada_raio.get())
        except ValueError:
            messagebox.showerror("Erro", "O Raio deve ser numérico!")
            self.attributes("-topmost", True)
            return

        if not nome:
            messagebox.showerror("Erro", "O modelo precisa de um nome!")
            self.attributes("-topmost", True)
            return

        if self.editando_modelo:
            if nome != self.editando_modelo and (nome == "Personalizado" or nome in self.tela_mapa.modelos_bases):
                messagebox.showerror("Erro", "Nome de modelo inválido ou já existente.")
                self.attributes("-topmost", True)
                return
            self.tela_mapa.atualizar_modelo_base(self.editando_modelo, nome, raio)
        else:
            if nome == "Personalizado" or nome in self.tela_mapa.modelos_bases:
                messagebox.showerror("Erro", "Nome de modelo inválido ou já existente.")
                self.attributes("-topmost", True)
                return
            self.tela_mapa.adicionar_modelo_base(nome, raio)
            
        self.destroy()
