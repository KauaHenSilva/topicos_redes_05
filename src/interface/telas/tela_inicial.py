import customtkinter as ctk
from tkinter import messagebox

class TelaInicial:
    def __init__(self, parent, app):
        self.parent = parent 
        self.app = app       
        self.construir_tela()

    def construir_tela(self):
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_titulo = ctk.CTkLabel(self.frame, text="Configuração Global", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.pack(pady=(30, 20), padx=40)

        self.entrada_largura = ctk.CTkEntry(self.frame, placeholder_text="Largura do Mapa (km)", width=250)
        self.entrada_largura.pack(pady=10, padx=40)

        self.entrada_altura = ctk.CTkEntry(self.frame, placeholder_text="Altura do Mapa (km)", width=250)
        self.entrada_altura.pack(pady=10, padx=40)

        self.btn_avancar = ctk.CTkButton(self.frame, text="Avançar para o Mapa", command=self.salvar_e_avancar)
        self.btn_avancar.pack(pady=(30, 30), padx=40)

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