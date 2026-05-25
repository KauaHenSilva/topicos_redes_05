from pathlib import Path
import sys

import customtkinter as ctk
from src.interface.telas.tela_inicial import TelaInicial
from src.interface.telas.tela_mapa import TelaMapa

# Tema inicial
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

class InterfaceSimulador(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("Simulador de Drones - Configuração")
        self.geometry("800x600")
        self.minsize(600, 500) # Evita que a janela fique pequena demais e quebre o layout
        
        # Dicionário global de dados
        self.dados_simulacao = {
            "numero_drones": 0,
            "tamanho_ambiente": [0, 0],
            "Pontos": {},
            "drones": {}
        }
        self.caminho_configuracao_atual = Path("config/config.json")
        self.diretorio_saida = Path("saida")

        # Switch para alternar Tema (Canto superior direito)
        self.switch_tema = ctk.CTkSwitch(self, text="Modo Claro", command=self.alternar_tema)
        self.switch_tema.pack(pady=15, padx=20, anchor="ne") # 'ne' = nordeste (topo direito)

        # Container principal onde as telas vão "trocar"
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Chama a primeira tela
        self.mostrar_tela_inicial()

    def alternar_tema(self):
        # Verifica qual modo está ativo e inverte
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self.switch_tema.configure(text="Modo Escuro")
        else:
            ctk.set_appearance_mode("Dark")
            self.switch_tema.configure(text="Modo Claro")

    def limpar_container(self):
        # Destrói tudo que está desenhado no container antes de carregar nova tela
        for widget in self.container.winfo_children():
            widget.destroy()

    def mostrar_tela_inicial(self):
        self.limpar_container()
        TelaInicial(self.container, self) # Passa o container e o app global

    def mostrar_tela_mapa(self):
        self.limpar_container()
        print("Indo para o Mapa com os dados temporários:", self.dados_simulacao)
        TelaMapa(self.container, self)

if __name__ == "__main__":
    app = InterfaceSimulador()
    app.mainloop()
