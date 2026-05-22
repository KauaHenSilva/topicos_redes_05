import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox

from src.interface.utils.gerador_json import carregar_configuracao_interface

class TelaInicial:
    def __init__(self, parent, app):
        self.parent = parent 
        self.app = app       
        self.construir_tela()

    def construir_tela(self):
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # --- TÍTULO E SUBTÍTULO (Upgrade 3) ---
        self.lbl_titulo = ctk.CTkLabel(self.frame, text="Configuração Global", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.pack(pady=(30, 5), padx=40)

        texto_dica = ("Dica: Mapas quadrados são melhores para visualização em modo janela. "
                      "Mapas retangulares horizontais são melhores para visualização em tela cheia.")
        
        self.lbl_subtitulo = ctk.CTkLabel(
            self.frame, 
            text=texto_dica, 
            text_color="gray", 
            font=ctk.CTkFont(size=12), 
            wraplength=260, # Quebra o texto para não esticar a janela
            justify="center"
        )
        self.lbl_subtitulo.pack(pady=(0, 20), padx=40)

        # --- LARGURA (Upgrade 1) ---
        self.lbl_largura = ctk.CTkLabel(self.frame, text="Largura do Mapa (km):", text_color="gray", anchor="w")
        self.lbl_largura.pack(padx=40, fill="x")
        self.entrada_largura = ctk.CTkEntry(self.frame, placeholder_text="ex: 200.0", width=260)
        self.entrada_largura.pack(pady=(0, 15), padx=40)

        # --- ALTURA (Upgrade 1) ---
        self.lbl_altura = ctk.CTkLabel(self.frame, text="Altura do Mapa (km):", text_color="gray", anchor="w")
        self.lbl_altura.pack(padx=40, fill="x")
        self.entrada_altura = ctk.CTkEntry(self.frame, placeholder_text="ex: 200.0", width=260)
        self.entrada_altura.pack(pady=(0, 20), padx=40)

        # --- BOTÕES (Upgrade 4 - Mesma largura das caixas) ---
        self.btn_avancar = ctk.CTkButton(
            self.frame, 
            text="Avançar para o Mapa", 
            width=260, 
            command=self.salvar_e_avancar
        )
        self.btn_avancar.pack(pady=(10, 10), padx=40)

        self.btn_carregar = ctk.CTkButton(
            self.frame,
            text="Carregar Configuração",
            width=260,
            fg_color="#555555",
            hover_color="#333333",
            command=self.carregar_configuracao,
        )
        self.btn_carregar.pack(pady=(0, 30), padx=40)

    def salvar_e_avancar(self):
        largura = self.entrada_largura.get()
        altura = self.entrada_altura.get()

        try:
            largura = float(largura)
            altura = float(altura)
            if largura <= 0 or altura <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos e maiores que zero.")
            return

        self.app.dados_simulacao["tamanho_ambiente"] = [largura, altura]
        # Deixamos o numero_drones para ser preenchido dinamicamente depois!
        
        self.app.mostrar_tela_mapa()

    def carregar_configuracao(self):
        caminho = filedialog.askopenfilename(
            title="Escolha uma configuração",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            self.app.dados_simulacao = carregar_configuracao_interface(caminho)
        except (OSError, ValueError) as erro:
            messagebox.showerror("Erro", f"Não foi possível carregar a configuração:\n{erro}")
            return

        self.app.caminho_configuracao_atual = Path(caminho)
        self.app.mostrar_tela_mapa()