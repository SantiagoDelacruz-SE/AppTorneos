import customtkinter as ctk
import random
from tkinter import messagebox, simpledialog

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# --- VENTANA DE PODIO ---
class VictoryWindow(ctk.CTkToplevel):
    def __init__(self, ranking, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("¡PODIO FINAL!")
        self.geometry("700x500")
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="🏆 CUADRO DE HONOR 🏆", font=("Arial", 28, "bold")).pack(pady=20)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both")
        container.grid_columnconfigure((0, 1, 2), weight=1)

        puestos = [
            {"idx": 1, "color": "#c0c0c0", "emoji": "🥈", "col": 0, "size": 25},
            {"idx": 0, "color": "#ffd700", "emoji": "🏆", "col": 1, "size": 35},
            {"idx": 2, "color": "#cd7f32", "emoji": "🥉", "col": 2, "size": 25}
        ]

        for p in puestos:
            if len(ranking) > p["idx"]:
                j = ranking[p["idx"]]
                f = ctk.CTkFrame(container, fg_color="transparent")
                f.grid(row=0, column=p["col"], padx=10, sticky="s")
                ctk.CTkLabel(f, text=p["emoji"], font=("Arial", 80)).pack()
                ctk.CTkLabel(f, text=j['nombre'], font=("Arial", p["size"], "bold"), text_color=p["color"]).pack()
                ctk.CTkLabel(f, text=f"{j['puntos']} Puntos", font=("Arial", 16)).pack()


# --- APP PRINCIPAL ---
class MTGManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("El Gremio - Tournament Manager")
        self.geometry("1200x850")

        self.jugadores = []
        self.ronda_actual = 0
        self.mesas_guardadas = 0
        self.total_mesas_ronda = 0

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

        # Botón extra para editar puntos (Instrucción)
        ctk.CTkLabel(self.sidebar, text="* Doble clic en fila para editar puntos", font=("Arial", 10, "italic"),
                     text_color="gray").pack(side="bottom", pady=10)

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tab_rank = self.tabs.add("Standings (OMWP)")
        self.tab_mesas = self.tabs.add("Mesas de la Ronda")

        self.scroll_rank = ctk.CTkScrollableFrame(self.tab_rank, fg_color="transparent")
        self.scroll_rank.pack(fill="both", expand=True)
        self.scroll_mesas = ctk.CTkScrollableFrame(self.tab_mesas)
        self.scroll_mesas.pack(fill="both", expand=True)

        self.actualizar_standings()

    def agregar_jugador(self):
        nom = self.entry_nombre.get().strip()
        if nom and not any(j['nombre'].lower() == nom.lower() for j in self.jugadores):
            self.jugadores.append({"nombre": nom, "puntos": 0, "oponentes": [], "rondas_jugadas": 0, "omwp": 0.0})
            self.entry_nombre.delete(0, 'end')
            self.actualizar_standings()
        self.entry_nombre.focus()

    def editar_puntos_manual(self, jugador_nombre):
        """Abre un diálogo para editar los puntos de un jugador específico."""
        jugador = next((j for j in self.jugadores if j['nombre'] == jugador_nombre), None)
        if jugador:
            nuevo_valor = simpledialog.askinteger("Editar Puntos", f"Nuevos puntos para {jugador_nombre}:",
                                                  initialvalue=jugador['puntos'])
            if nuevo_valor is not None:
                jugador['puntos'] = nuevo_valor
                self.actualizar_standings()

    def calcular_omwp(self):
        for j in self.jugadores:
            if not j["oponentes"]:
                j["omwp"] = 0.0
                continue
            porcentajes = []
            for nom_op in j["oponentes"]:
                op = next((obj for obj in self.jugadores if obj["nombre"] == nom_op), None)
                if op and op["rondas_jugadas"] > 0:
                    win_rate = op["puntos"] / (op["rondas_jugadas"] * 4)
                    porcentajes.append(max(win_rate, 0.33))
            j["omwp"] = (sum(porcentajes) / len(porcentajes)) * 100 if porcentajes else 0.0

    def actualizar_standings(self):
        self.calcular_omwp()
        for w in self.scroll_rank.winfo_children(): w.destroy()

        h = ctk.CTkFrame(self.scroll_rank, fg_color="#1f538d", height=40)
        h.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(h, text="POS", width=60, font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(h, text="JUGADOR", width=250, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(h, text="OMWP%", width=100, font=("Arial", 12, "bold")).pack(side="right", padx=10)
        ctk.CTkLabel(h, text="PUNTOS", width=80, font=("Arial", 12, "bold")).pack(side="right", padx=10)

        ranking = sorted(self.jugadores, key=lambda x: (x['puntos'], x['omwp']), reverse=True)

        for i, j in enumerate(ranking, 1):
            row = ctk.CTkFrame(self.scroll_rank, height=45, fg_color="#333" if i % 2 == 0 else "#2b2b2b")
            row.pack(fill="x", pady=2, padx=5)

            # Hacer que la fila sea clickeable para editar
            row.bind("<Double-Button-1>", lambda e, n=j['nombre']: self.editar_puntos_manual(n))

            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
            color = "#ffd700" if i == 1 else "#c0c0c0" if i == 2 else "#cd7f32" if i == 3 else "white"

            lbl_pos = ctk.CTkLabel(row, text=icon, width=60, text_color=color,
                                   font=("Arial", 18 if i <= 3 else 14, "bold"))
            lbl_pos.pack(side="left", padx=10)
            lbl_pos.bind("<Double-Button-1>", lambda e, n=j['nombre']: self.editar_puntos_manual(n))

            lbl_nom = ctk.CTkLabel(row, text=j['nombre'], width=250, anchor="w", font=("Arial", 15))
            lbl_nom.pack(side="left", padx=10)
            lbl_nom.bind("<Double-Button-1>", lambda e, n=j['nombre']: self.editar_puntos_manual(n))

            ctk.CTkLabel(row, text=f"{j['omwp']:.2f}%", width=100, text_color="#aaa").pack(side="right", padx=10)
            ctk.CTkLabel(row, text=str(j['puntos']), width=80, font=("Arial", 15, "bold")).pack(side="right", padx=10)

    def nueva_ronda(self):
        if self.ronda_actual > 0 and self.mesas_guardadas < self.total_mesas_ronda:
            messagebox.showwarning("Mesas Pendientes", "Guarda todas las mesas antes de continuar.")
            return

        total_config = int(self.spin_rondas.get())
        if self.ronda_actual >= total_config:
            VictoryWindow(sorted(self.jugadores, key=lambda x: (x['puntos'], x['omwp']), reverse=True), self)
            return

        self.ronda_actual += 1
        self.mesas_guardadas = 0
        self.btn_iniciar.configure(state="disabled", text="CARGANDO...")

        pool = self.jugadores[:]
        if self.pairing_mode.get() == "Suizo":
            pool.sort(key=lambda x: (x['puntos'], x['omwp']), reverse=True)
        else:
            random.shuffle(pool)

        for w in self.scroll_mesas.winfo_children(): w.destroy()

        num_j = len(pool)
        mesas_finales = []
        if num_j % 4 == 0:
            mesas_finales = [4] * (num_j // 4)
        elif num_j == 6:
            mesas_finales = [3, 3]
        elif num_j % 4 == 3:
            mesas_finales = [4] * (num_j // 4) + [3]
        elif num_j % 4 == 2:
            mesas_finales = [4] * (num_j // 4 - 1) + [3, 3]
        elif num_j % 4 == 1:
            mesas_finales = [4] * (num_j // 4 - 2) + [3, 3, 3] if num_j >= 9 else [3, 2]
        else:
            mesas_finales = [num_j]

        self.total_mesas_ronda = len(mesas_finales)
        m_idx = 1
        for tam in mesas_finales:
            grupo = [pool.pop(0) for _ in range(tam)]
            for p in grupo:
                otros = [o["nombre"] for o in grupo if o["nombre"] != p["nombre"]]
                for jr in self.jugadores:
                    if jr["nombre"] == p["nombre"]:
                        jr["oponentes"].extend(otros)
                        jr["rondas_jugadas"] += 1
            self.crear_tarjeta_mesa(m_idx, grupo)
            m_idx += 1
        self.tabs.set("Mesas de la Ronda")

    def crear_tarjeta_mesa(self, num, grupo):
        card = ctk.CTkFrame(self.scroll_mesas, border_width=1, border_color="#555")
        card.pack(pady=10, padx=10, fill="x")
        f_info = ctk.CTkFrame(card, fg_color="transparent")
        f_info.pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(f_info, text=f"MESA {num}", font=("Arial", 18, "bold"), text_color="#3b8ed0").pack(anchor="w")
        for j in grupo:
            ctk.CTkLabel(f_info, text=f"• {j['nombre']} ({j['puntos']} pts)", font=("Arial", 14)).pack(anchor="w")

        f_res = ctk.CTkFrame(card, fg_color="transparent")
        f_res.pack(side="right", padx=20, pady=15)
        combos, nombres, historial = [], [j['nombre'] for j in grupo], {}

        for i in range(len(grupo)):
            row = ctk.CTkFrame(f_res, fg_color="transparent")
            row.pack(pady=2)
            ctk.CTkLabel(row, text=f"{i + 1}º:", width=40).pack(side="left")
            cb = ctk.CTkOptionMenu(row, values=["..."] + nombres, width=150,
                                   command=lambda _: self.actualizar_opciones(combos, nombres))
            cb.set("...")
            cb.pack(side="left")
            combos.append(cb)

        btn = ctk.CTkButton(f_res, text="Guardar", width=100)
        btn.configure(command=lambda: self.guardar_mesa(combos, card, btn, historial))
        btn.pack(pady=10)

    def actualizar_opciones(self, combos, nombres):
        sel = [c.get() for c in combos if c.get() != "..."]
        for cb in combos:
            val = cb.get()
            cb.configure(values=["..."] + [n for n in nombres if n not in sel or n == val])

    def guardar_mesa(self, combos, frame, btn, historial):
        if btn.cget("text") == "Editar":
            for n, p in historial.items():
                for j in self.jugadores:
                    if j['nombre'] == n: j['puntos'] -= p
            historial.clear()
            frame.configure(fg_color="#2b2b2b")
            btn.configure(text="Guardar", fg_color="#3b8ed0")
            for cb in combos: cb.configure(state="normal")
            self.mesas_guardadas -= 1
            self.actualizar_standings()
            return

        resultados = [c.get() for c in combos]
        if "..." in resultados: return
        puntos_val = [4, 3, 2, 1]
        for i, nombre in enumerate(resultados):
            for j in self.jugadores:
                if j['nombre'] == nombre:
                    j['puntos'] += puntos_val[i]
                    historial[nombre] = puntos_val[i]

        self.mesas_guardadas += 1
        frame.configure(fg_color="#1e3d24")
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