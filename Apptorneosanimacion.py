import customtkinter as ctk
import tkinter as tk
import random
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageSequence
import pygame
import os

# Inicializar Audio
pygame.mixer.init()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MTGManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MTG Manager Pro - Cinematic Edition")
        self.geometry("1200x850")

        self.jugadores = []
        self.ronda_actual = 0
        self.mesas_guardadas = 0
        self.total_mesas_ronda = 0
        self.animacion_activa = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="REGISTRO", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        self.entry_nombre = ctk.CTkEntry(self.sidebar, placeholder_text="Nombre del jugador")
        self.entry_nombre.pack(pady=10, padx=20, fill="x")
        self.entry_nombre.bind("<Return>", lambda e: self.agregar_jugador())

        ctk.CTkButton(self.sidebar, text="Añadir (Enter)", command=self.agregar_jugador).pack(padx=20, fill="x")

        self.pairing_mode = ctk.CTkSegmentedButton(self.sidebar, values=["Aleatorio", "Suizo"])
        self.pairing_mode.set("Aleatorio")
        self.pairing_mode.pack(pady=20, padx=20, fill="x")

        self.spin_rondas = ctk.CTkOptionMenu(self.sidebar, values=["1", "2", "3", "4", "5", "6"])
        self.spin_rondas.set("4")
        self.spin_rondas.pack(padx=20, fill="x")

        self.btn_iniciar = ctk.CTkButton(self.sidebar, text="GENERAR RONDA 1", fg_color="#28a745",
                                         command=self.nueva_ronda)
        self.btn_iniciar.pack(pady=20, padx=20, fill="x")

        # --- MAIN ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tab_rank = self.tabs.add("Standings (OMWP)")
        self.tab_mesas = self.tabs.add("Mesas")

        self.container_standings = ctk.CTkFrame(self.tab_rank, fg_color="transparent")
        self.container_standings.pack(fill="both", expand=True)

        self.scroll_rank = ctk.CTkScrollableFrame(self.container_standings, fg_color="transparent")
        self.scroll_rank.pack(fill="both", expand=True)
        self.scroll_mesas = ctk.CTkScrollableFrame(self.tab_mesas)
        self.scroll_mesas.pack(fill="both", expand=True)

        self.actualizar_standings()

    def reproducir_sonido(self, archivo):
        try:
            if os.path.exists(archivo):
                pygame.mixer.music.load(archivo)
                pygame.mixer.music.play()
        except:
            pass

    def agregar_jugador(self):
        nom = self.entry_nombre.get().strip()
        if nom and not any(j['nombre'].lower() == nom.lower() for j in self.jugadores):
            self.jugadores.append({"nombre": nom, "puntos": 0, "oponentes": [], "rondas_jugadas": 0, "omwp": 0.0})
            self.entry_nombre.delete(0, 'end')
            self.actualizar_standings()

    def actualizar_standings(self):
        if self.animacion_activa: return
        for w in self.scroll_rank.winfo_children(): w.destroy()

        ranking = sorted(self.jugadores, key=lambda x: (x['puntos'], x['omwp']), reverse=True)
        for i, j in enumerate(ranking, 1):
            row = ctk.CTkFrame(self.scroll_rank, height=45, fg_color="#333" if i % 2 == 0 else "#2b2b2b")
            row.pack(fill="x", pady=2, padx=5)
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
            ctk.CTkLabel(row, text=icon, width=60, font=("Arial", 16, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=j['nombre'], width=250, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=str(j['puntos']), width=80, font=("Arial", 15, "bold")).pack(side="right", padx=10)

    def nueva_ronda(self):
        if self.ronda_actual > 0 and self.mesas_guardadas < self.total_mesas_ronda:
            messagebox.showwarning("Aviso", "Guarda todas las mesas.")
            return

        total_conf = int(self.spin_rondas.get())
        if self.ronda_actual >= total_conf:
            self.preparar_celebracion()
            return

        # AUDIO AL GENERAR RONDA
        self.reproducir_sonido("ronda.wav")  # Asegúrate de tener este archivo o cambia el nombre

        self.ronda_actual += 1
        self.mesas_guardadas = 0
        self.btn_iniciar.configure(state="disabled", text="EN CURSO...")

        pool = self.jugadores[:]
        if self.pairing_mode.get() == "Suizo":
            pool.sort(key=lambda x: (x['puntos'], x['omwp']), reverse=True)
        else:
            random.shuffle(pool)

        for w in self.scroll_mesas.winfo_children(): w.destroy()

        # Reparto 3-3 si son 6
        n = len(pool)
        tams = [3, 3] if n == 6 else ([4] * (n // 4) + ([n % 4] if n % 4 != 0 else []))
        if n > 4 and n % 4 == 1: tams = [4] * (len(tams) - 2) + [3, 2]  # Ajuste simple

        self.total_mesas_ronda = len(tams)
        for i, tam in enumerate(tams, 1):
            grupo = [pool.pop(0) for _ in range(tam)]
            self.crear_tarjeta_mesa(i, grupo)
        self.tabs.set("Mesas")

    def preparar_celebracion(self):
        self.animacion_activa = True
        self.tabs.set("Standings (OMWP)")
        self.scroll_rank.pack_forget()

        self.f_celebracion = ctk.CTkFrame(self.container_standings, fg_color="transparent")
        self.f_celebracion.pack(expand=True, fill="both")

        # Clic para saltar o avanzar
        self.f_celebracion.bind("<Button-1>", lambda e: self.revelar_siguiente_puesto())

        self.ranking_final = sorted(self.jugadores, key=lambda x: (x['puntos'], x['omwp']), reverse=True)
        self.puestos_revelados = 0

        # Audio de victoria
        self.reproducir_sonido("ganador.wav")
        self.revelar_siguiente_puesto()

    def revelar_siguiente_puesto(self):
        """Maneja la aparición tipo Fade In de los 3 primeros."""
        if self.puestos_revelados >= 3 or self.puestos_revelados >= len(self.ranking_final):
            self.cerrar_celebracion()
            return

        # Datos del puesto actual (Empezamos por el 3º, luego 2º, luego 1º para drama)
        # O si prefieres 1, 2, 3:
        idx = self.puestos_revelados
        j = self.ranking_final[idx]
        emojis = ["🥇", "🥈", "🥉"]
        colores = ["#ffd700", "#c0c0c0", "#cd7f32"]

        lbl = ctk.CTkLabel(self.f_celebracion, text=f"{emojis[idx]} {j['nombre']}",
                           font=("Arial", 40 + (20 if idx == 0 else 0), "bold"),
                           text_color="#242424")  # Empieza invisible (color del fondo)
        lbl.pack(pady=10)

        # Iniciar Fade In
        self.fade_in(lbl, colores[idx])
        self.puestos_revelados += 1

    def fade_in(self, widget, color_final, step=0):
        """Simula un fade in cambiando el color del texto gradualmente."""
        if step <= 10:
            # Aquí podrías usar una librería de colores, pero para simplicidad
            # saltamos del fondo al color final en el paso 10
            if step == 10:
                widget.configure(text_color=color_final)
            else:
                self.after(50, lambda: self.fade_in(widget, color_final, step + 1))

    def cerrar_celebracion(self):
        self.animacion_activa = False
        if hasattr(self, 'f_celebracion'): self.f_celebracion.destroy()
        self.scroll_rank.pack(fill="both", expand=True)
        self.actualizar_standings()
        self.btn_iniciar.configure(text="TORNEO FINALIZADO", state="disabled")

    # (Funciones de mesa se mantienen igual)
    def crear_tarjeta_mesa(self, num, grupo):
        card = ctk.CTkFrame(self.scroll_mesas, border_width=1, border_color="#555")
        card.pack(pady=10, padx=10, fill="x")
        f_info = ctk.CTkFrame(card, fg_color="transparent");
        f_info.pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(f_info, text=f"MESA {num}", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(anchor="w")
        for j in grupo: ctk.CTkLabel(f_info, text=f"• {j['nombre']}").pack(anchor="w")
        f_res = ctk.CTkFrame(card, fg_color="transparent");
        f_res.pack(side="right", padx=20, pady=15)
        combos, nombres, historial = [], [j['nombre'] for j in grupo], {}
        for i in range(len(grupo)):
            row = ctk.CTkFrame(f_res, fg_color="transparent");
            row.pack()
            cb = ctk.CTkOptionMenu(row, values=["..."] + nombres, width=150,
                                   command=lambda _: self.actualizar_opciones(combos, nombres))
            cb.set("...");
            cb.pack(side="left", pady=2);
            combos.append(cb)
        btn = ctk.CTkButton(f_res, text="Guardar", width=100,
                            command=lambda: self.guardar_mesa(combos, card, btn, historial))
        btn.pack(pady=10)

    def actualizar_opciones(self, combos, nombres):
        selec = [c.get() for c in combos if c.get() != "..."]
        for cb in combos:
            val = cb.get()
            cb.configure(values=["..."] + [n for n in nombres if n not in selec or n == val])

    def guardar_mesa(self, combos, frame, btn, historial):
        if btn.cget("text") == "Editar":
            for n, p in historial.items():
                for j in self.jugadores:
                    if j['nombre'] == n: j['puntos'] -= p
            historial.clear();
            frame.configure(fg_color="#2b2b2b");
            btn.configure(text="Guardar", fg_color="#3b8ed0")
            for cb in combos: cb.configure(state="normal")
            self.mesas_guardadas -= 1;
            self.actualizar_standings();
            return
        res = [c.get() for c in combos]
        if "..." in res: return
        pts_v = [4, 3, 2, 1]
        for i, nom in enumerate(res):
            for j in self.jugadores:
                if j['nombre'] == nom: j['puntos'] += pts_v[i]; historial[nom] = pts_v[i]
        self.mesas_guardadas += 1;
        frame.configure(fg_color="#1e3d24");
        btn.configure(text="Editar", fg_color="#555")
        for cb in combos: cb.configure(state="disabled")
        self.actualizar_standings()
        if self.mesas_guardadas == self.total_mesas_ronda:
            txt = f"GENERAR RONDA {self.ronda_actual + 1}" if self.ronda_actual < int(
                self.spin_rondas.get()) else "FINALIZAR TORNEO"
            self.btn_iniciar.configure(state="normal", text=txt)


if __name__ == "__main__":
    app = MTGManagerApp()
    app.mainloop()