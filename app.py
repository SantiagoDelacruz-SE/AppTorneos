import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# Configuration
st.set_page_config(page_title="Commander Tournament Pro", page_icon="🏆", layout="wide")

# CSS for themes
def get_css(theme):
    if theme == "light":
        return """
        <style>
        .podium-card { text-align: center; padding: 15px; border-radius: 15px; background-color: #F0F0F0; border: 2px solid #CCC; margin-bottom: 10px; }
        .gold { border-color: #FFD700; box-shadow: 0px 0px 15px #FFD700; }
        .silver { border-color: #C0C0C0; box-shadow: 0px 0px 10px #C0C0C0; }
        .bronze { border-color: #CD7F32; box-shadow: 0px 0px 10px #CD7F32; }
        .commander-name { color: #666; font-style: italic; font-size: 0.85em; margin-bottom: 5px; }
        .dropped-player { color: #CC2222; text-decoration: line-through; }
        </style>
        """
    else:
        return """
        <style>
        .podium-card { text-align: center; padding: 15px; border-radius: 15px; background-color: #1E1E1E; border: 2px solid #464855; margin-bottom: 10px; }
        .gold { border-color: #FFD700; box-shadow: 0px 0px 15px #FFD700; }
        .silver { border-color: #C0C0C0; box-shadow: 0px 0px 10px #C0C0C0; }
        .bronze { border-color: #CD7F32; box-shadow: 0px 0px 10px #CD7F32; }
        .commander-name { color: #888; font-style: italic; font-size: 0.85em; margin-bottom: 5px; }
        .dropped-player { color: #FF4444; text-decoration: line-through; }
        </style>
        """

theme = st.session_state.get("theme", "dark")
st.markdown(get_css(theme), unsafe_allow_html=True)

DB_FILE = "torneo_data.json"

# --- Persistence ---
def save_data():
    try:
        data = {
            "jugadores": st.session_state.jugadores,
            "historial": st.session_state.historial,
            "ronda_actual": st.session_state.ronda_actual,
            "puntos_config": st.session_state.puntos_config,
            "finalizado": st.session_state.finalizado,
            "mesas_activas": st.session_state.mesas_activas,
            "max_rondas": st.session_state.get("max_rondas", 0),
            "dropped_players": st.session_state.get("dropped_players", []),
            "theme": st.session_state.get("theme", "dark")
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error("Error guardando datos: " + str(e))

def load_data():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    st.session_state[k] = v
    except Exception as e:
        st.error("Error cargando datos: " + str(e))

# --- Initialization ---
def init_session_state():
    if 'jugadores' not in st.session_state:
        defaults = {
            "jugadores": {},
            "historial": [],
            "ronda_actual": 1,
            "puntos_config": {"1°": 4, "2°": 3, "3°": 2, "4°": 1},
            "finalizado": False,
            "mesas_activas": None,
            "max_rondas": 0,
            "dropped_players": [],
            "theme": "dark"
        }
        for k, v in defaults.items():
            st.session_state[k] = v
        load_data()

init_session_state()

# --- Logic Functions ---
def calculate_omw(player_name):
    datos = st.session_state.jugadores.get(player_name)
    if not datos or not datos.get("oponentes") or datos["partidas"] == 0:
        return 0.0
    wrs = []
    for op_n in datos["oponentes"]:
        op = st.session_state.jugadores.get(op_n)
        if op and op.get("partidas", 0) > 0:
            val = op["puntos"] / (op["partidas"] * 4)
            wrs.append(max(val, 0.33))
    return sum(wrs) / len(wrs) if wrs else 0.0

def generate_pairings(mode):
    nombres = [n for n, d in st.session_state.jugadores.items()
               if n not in st.session_state.dropped_players]

    if mode == "Suizo":
        nombres.sort(key=lambda x: (st.session_state.jugadores[x]["puntos"], calculate_omw(x)), reverse=True)
    else:
        random.shuffle(nombres)

    mesas = []
    i = 0
    while i < len(nombres):
        restantes = len(nombres) - i
        if restantes == 1:
            jugador_bye = nombres[i]
            st.session_state.jugadores[jugador_bye]["puntos"] += st.session_state.puntos_config["1°"]
            st.session_state.jugadores[jugador_bye]["partidas"] += 1
            st.session_state.jugadores[jugador_bye]["oponentes"].append("BYE")
            st.success("Bye para " + jugador_bye)
            i += 1
            continue
        elif restantes == 2:
            tam = 2
        elif restantes == 3:
            tam = 3
        elif restantes == 5:
            tam = 3
        else:
            tam = 4

        mesas.append(nombres[i:i + tam])
        i += tam
    return mesas

def get_player_match_history(player_name):
    history = []
    for ronda_idx, ronda in enumerate(st.session_state.historial):
        for mesa_idx, mesa_data in enumerate(ronda):
            if player_name in mesa_data.get("mesa", []):
                pos = mesa_data.get("posiciones", {}).get(player_name, "N/A")
                try:
                    pts_key = str(pos) + "°"
                    pts = st.session_state.puntos_config.get(pts_key, 0)
                except:
                    pts = 0
                history.append({
                    "Ronda": ronda_idx + 1,
                    "Mesa": mesa_idx + 1,
                    "Posicion": str(pos) + "°",
                    "Puntos": pts,
                    "Oponentes": [j for j in mesa_data.get("mesa", []) if j != player_name]
                })
    return history

# --- Export Functions ---
def export_to_csv():
    if not st.session_state.historial:
        return None
    output = []
    output.append("Ronda,Mesa,Jugador,Posicion,Puntos,Comandante")

    for ronda_idx, ronda in enumerate(st.session_state.historial):
        for mesa_idx, mesa_data in enumerate(ronda):
            for jug, pos in mesa_data.get("posiciones", {}).items():
                datos = st.session_state.jugadores.get(jug, {})
                try:
                    pts_key = str(pos) + "°"
                    pts = st.session_state.puntos_config.get(pts_key, 0)
                except:
                    pts = 0
                comandante = str(datos.get('comandante', 'N/A'))
                line = str(ronda_idx + 1) + "," + str(mesa_idx + 1) + "," + jug + "," + str(pos) + "," + str(pts) + "," + comandante
                output.append(line)

    return "\n".join(output)

def get_final_standings():
    data_final = []
    for nom, stats in st.session_state.jugadores.items():
        if nom in st.session_state.dropped_players:
            continue
        omw = calculate_omw(nom)
        data_final.append({
            "Jugador": nom,
            "Puntos": stats.get("puntos", 0),
            "OMW%": "{:.3f}".format(omw),
            "Partidas": stats.get("partidas", 0),
            "Comandante": stats.get("comandante", "N/A")
        })
    if not data_final:
        return pd.DataFrame(columns=["Jugador", "Puntos", "OMW%", "Partidas", "Comandante"])
    return pd.DataFrame(data_final).sort_values(by=["Puntos", "OMW%"], ascending=False)

# --- Sidebar ---
def render_sidebar():
    with st.sidebar:
        st.title("Administracion")
        es_admin = st.toggle("Modo Administrador", value=False)

        if es_admin:
            st.subheader("Configuracion Global")
            for k in ["1°", "2°", "3°", "4°"]:
                key_name = "cfg_" + k
                st.session_state.puntos_config[k] = st.number_input(
                    "Pts " + k, value=st.session_state.puntos_config[k], key=key_name
                )

            st.subheader("Configuracion de Rondas")
            modo_rondas = st.radio("Modo de Rondas", ["Dinamico", "Fijo"], key="modo_rondas")
            if modo_rondas == "Fijo":
                st.session_state.max_rondas = st.number_input(
                    "Cantidad de Rondas", min_value=1, max_value=20,
                    value=st.session_state.get("max_rondas", 5) or 5, key="max_rnd_input"
                )
            if st.button("Resetear Torneo", type="secondary"):
                confirm = st.checkbox("Confirmar resetear todo el torneo", key="confirm_reset")
                if confirm:
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                    st.session_state.clear()
                    init_session_state()
                    st.rerun()

        st.divider()
        st.subheader("Standings")

        jug_sort = sorted(
            [(n, d) for n, d in st.session_state.jugadores.items()
             if n not in st.session_state.dropped_players],
            key=lambda x: (x[1]["puntos"], calculate_omw(x[0]), x[0]),
            reverse=True
        )

        if jug_sort:
            standings_data = []
            for i, (n, d) in enumerate(jug_sort):
                standings_data.append({
                    "Pos": i + 1,
                    "Jugador": n,
                    "Pts": d["puntos"],
                    "OMW%": "{:.3f}".format(calculate_omw(n))
                })
            df_standings = pd.DataFrame(standings_data)
            df_standings.set_index("Pos", inplace=True)
            st.dataframe(df_standings, use_container_width=True, height=300)

        if st.session_state.dropped_players:
            with st.expander("Jugadores Retirados"):
                for p in st.session_state.dropped_players:
                    st.write("~~" + p + "~~")

        return es_admin

# --- Main App ---
def main():
    es_admin = render_sidebar()

    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1>Commander Tournament Manager</h1>
            <p style='color: #888;'>Gestiona torneos de Magic: The Gathering Commander</p>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.finalizado:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Jugadores", "Mesas", "Historial", "Perfiles", "Exportar"]
        )

        # --- TAB 1: PLAYERS ---
        with tab1:
            c1, c2 = st.columns([1, 2])

            with c1:
                st.subheader("Inscripcion")
                n_j = st.text_input("Nombre del Jugador", key="new_player_name")
                b_c = st.text_input("Comandante", key="new_player_commander")

                colores_insc = []
                if es_admin:
                    colores_insc = st.multiselect("Colores del Comandante", ["Blanco", "Azul", "Negro", "Rojo", "Verde"], key="col_insc")

                if st.button("Añadir", key="add_player") and n_j:
                    if n_j in st.session_state.jugadores:
                        st.error("El jugador '" + n_j + "' ya esta inscrito.")
                    else:
                        st.session_state.jugadores[n_j] = {
                            "puntos": 0,
                            "comandante": b_c or "No especificado",
                            "colores": colores_insc,
                            "oponentes": [],
                            "partidas": 0
                        }
                        save_data()
                        st.rerun()

                if es_admin and st.session_state.jugadores:
                    st.divider()
                    st.subheader("Retirar Jugador")
                    drop_player = st.selectbox(
                        "Seleccionar jugador",
                        [p for p in st.session_state.jugadores.keys()
                         if p not in st.session_state.dropped_players],
                        key="drop_select"
                    )
                    if st.button("Retirar", type="secondary"):
                        st.session_state.dropped_players.append(drop_player)
                        save_data()
                        st.rerun()

            with c2:
                active_count = len(st.session_state.jugadores) - len(st.session_state.dropped_players)
                st.subheader("Jugadores Activos (" + str(active_count) + ")")

                jugadores_activos = {n: d for n, d in st.session_state.jugadores.items()
                                     if n not in st.session_state.dropped_players}

                if jugadores_activos:
                    cols = st.columns(3)
                    for i, (n, d) in enumerate(jugadores_activos.items()):
                        with cols[i % 3]:
                            with st.container(border=True):
                                st.markdown("<div style='text-align:center;font-size:2em;'>🃏</div>", unsafe_allow_html=True)
                                st.markdown("<h4 style='text-align:center;margin-bottom:2px;'>" + n + "</h4>", unsafe_allow_html=True)
                                st.markdown("<p style='text-align:center;color:#888;font-style:italic;margin-top:0;'>🎴 " + str(d.get('comandante', 'N/A')) + "</p>", unsafe_allow_html=True)
                                colores = d.get('colores', [])
                                if colores:
                                    mapa = {"Blanco": "#F8E7B4", "Azul": "#0E68AB", "Negro": "#1A1A1A", "Rojo": "#D3202A", "Verde": "#00733E"}
                                    letras = {"Blanco": "W", "Azul": "U", "Negro": "B", "Rojo": "R", "Verde": "G"}
                                    txt_color = {"Blanco": "#333", "Azul": "#FFF", "Negro": "#FFF", "Rojo": "#FFF", "Verde": "#FFF"}
                                    symbols = ""
                                    for c in colores:
                                        bg = mapa.get(c, "#888")
                                        l = letras.get(c, "?")
                                        tc = txt_color.get(c, "#FFF")
                                        symbols += "<span style='display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:4px;background:" + bg + ";color:" + tc + ";font-weight:bold;font-size:14px;margin:0 2px;border:1px solid #555;'>" + l + "</span>"
                                    st.markdown("<div style='text-align:center;margin:4px 0;'>" + symbols + "</div>", unsafe_allow_html=True)
                                st.metric("Puntos", d["puntos"], label_visibility="collapsed")

                                if es_admin:
                                    if st.button("🗑️", key="del_" + n, help="Eliminar jugador", type="secondary", use_container_width=True):
                                        del st.session_state.jugadores[n]
                                        if n in st.session_state.dropped_players:
                                            st.session_state.dropped_players.remove(n)
                                        save_data()
                                        st.rerun()

                                    with st.expander("Editar"):
                                        key_pts = "m_pts_" + n
                                        new_pts = st.number_input("Puntos", value=d["puntos"],
                                                                   key=key_pts, label_visibility="collapsed")
                                        if new_pts != d["puntos"]:
                                            st.session_state.jugadores[n]["puntos"] = new_pts
                                            save_data()

                                        key_cmd = "cmd_" + n
                                        new_cmd = st.text_input("Comandante", value=d.get("comandante", ""),
                                                                key=key_cmd, label_visibility="collapsed")
                                        colores_opts = ["Blanco", "Azul", "Negro", "Rojo", "Verde"]
                                        col_sel = st.multiselect("Colores", colores_opts, default=d.get("colores", []), key="col_" + n)
                                        if col_sel != d.get("colores", []):
                                            st.session_state.jugadores[n]["colores"] = col_sel
                                            save_data()

                                        if st.button("Actualizar", key="upd_cmd_" + n):
                                            if new_cmd:
                                                st.session_state.jugadores[n]["comandante"] = new_cmd
                                                save_data()
                                                st.rerun()

                    if es_admin and st.button("Guardar Cambios"):
                        save_data()
                else:
                    st.info("No hay jugadores inscritos.")

        # --- TAB 2: TABLES ---
        with tab2:
            st.subheader("Gestion de Mesas")

            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 2])

            with col_ctrl1:
                modo_emp = st.selectbox("Emparejamiento", ["Aleatorio", "Suizo"], key="modo_emparejamiento")

            active_players_count = len(st.session_state.jugadores) - len(st.session_state.dropped_players)

            with col_ctrl2:
                if st.button("Generar / Resetear Mesas", use_container_width=True, type="primary"):
                    if active_players_count < 2:
                        st.warning("Se requieren al menos 2 jugadores activos.")
                    else:
                        st.session_state.mesas_activas = generate_pairings(modo_emp)
                        save_data()
                        st.rerun()

            with col_ctrl3:
                if st.button("Terminar Ronda", use_container_width=True):
                    st.session_state.mesas_activas = None
                    save_data()
                    st.rerun()

            if st.session_state.mesas_activas:
                if es_admin:
                    with st.expander("Editar Mesas Manualmente", expanded=False):
                        for idx, mesa in enumerate(st.session_state.mesas_activas):
                            key_edit = "edit_m_" + str(idx)
                            st.session_state.mesas_activas[idx] = st.multiselect(
                                "Mesa " + str(idx + 1),
                                options=list(st.session_state.jugadores.keys()),
                                default=mesa,
                                key=key_edit
                            )
                        col_add, col_del = st.columns(2)
                        with col_add:
                            if st.button("Añadir Mesa"):
                                st.session_state.mesas_activas.append([])
                                st.rerun()
                        with col_del:
                            if st.button("Limpiar Mesas Vacias"):
                                st.session_state.mesas_activas = [m for m in st.session_state.mesas_activas if m]
                                st.rerun()

                with st.form("ronda_form"):
                    st.subheader("Resultados Ronda " + str(st.session_state.ronda_actual))

                    ronda_results = []

                    for idx, mesa in enumerate(st.session_state.mesas_activas):
                        if not mesa:
                            continue

                        st.markdown("### Mesa " + str(idx + 1))
                        cols = st.columns(len(mesa))

                        res_m = {}
                        for i, j in enumerate(mesa):
                            with cols[i]:
                                st.markdown("**" + j + "**")
                                key_sel = "r_" + str(idx) + "_" + str(j)
                                res_m[j] = st.selectbox(
                                    "Posicion",
                                    options=[1, 2, 3, 4][:len(mesa)],
                                    key=key_sel,
                                    label_visibility="collapsed"
                                )
                        ronda_results.append({"mesa": mesa, "posiciones": res_m})
                        st.divider()

                    submitted = st.form_submit_button("Finalizar Ronda y Sumar Puntos")

                    if submitted:
                        error = False
                        for res in ronda_results:
                            if None in res["posiciones"].values() or len(set(res["posiciones"].values())) != len(res["posiciones"]):
                                error = True
                                break

                        if error:
                            st.error("Todos los puestos deben estar llenos y no puede haber posiciones repetidas.")
                        else:
                            for m in ronda_results:
                                for jug, pos in m["posiciones"].items():
                                    pts_key = str(pos) + "°"
                                    if pts_key in st.session_state.puntos_config:
                                        st.session_state.jugadores[jug]["puntos"] += st.session_state.puntos_config[pts_key]
                                        st.session_state.jugadores[jug]["partidas"] += 1
                                        st.session_state.jugadores[jug]["oponentes"].extend(
                                            [o for o in m["mesa"] if o != jug]
                                        )

                            st.session_state.historial.append(ronda_results)
                            st.session_state.ronda_actual += 1
                            st.session_state.mesas_activas = None

                            if (st.session_state.get("modo_rondas") == "Fijo" and
                                st.session_state.max_rondas and
                                st.session_state.ronda_actual > st.session_state.max_rondas):
                                st.session_state.finalizado = True

                            save_data()
                            st.rerun()

            st.divider()
            if st.button("FINALIZAR TODO EL TORNEO", type="primary", use_container_width=True):
                st.session_state.finalizado = True
                save_data()
                st.rerun()

        # --- TAB 3: HISTORY ---
        with tab3:
            st.subheader("Historial de Rondas")
            if st.session_state.historial:
                for i, ronda in enumerate(st.session_state.historial):
                    with st.expander("Ronda " + str(i + 1)):
                        h_table = []
                        for m_idx, m_data in enumerate(ronda):
                            for jug, pos in m_data["posiciones"].items():
                                h_table.append({
                                    "Mesa": m_idx + 1,
                                    "Jugador": jug,
                                    "Lugar": str(pos) + "°",
                                    "Puntos": st.session_state.puntos_config.get(str(pos) + "°", 0)
                                })
                        if h_table:
                            df_h = pd.DataFrame(h_table)
                            st.dataframe(df_h, use_container_width=True, hide_index=True)
            else:
                st.info("No hay rondas jugadas aun.")

        # --- TAB 4: PROFILES ---
        with tab4:
            st.subheader("Perfiles de Jugadores")
            if st.session_state.jugadores:
                selected_player = st.selectbox(
                    "Seleccionar Jugador",
                    list(st.session_state.jugadores.keys()),
                    key="profile_select"
                )

                if selected_player:
                    d = st.session_state.jugadores[selected_player]
                    c1, c2 = st.columns([1, 2])

                    with c1:
                        st.metric("Puntos", d["puntos"])
                        st.metric("Partidas", d["partidas"])
                        st.write("**Comandante:** " + str(d.get('comandante', 'N/A')))
                        st.write("**OMW%:** {:.3f}".format(calculate_omw(selected_player)))

                    with c2:
                        st.subheader("Historial de Enfrentamientos")
                        history = get_player_match_history(selected_player)
                        if history:
                            for h in history:
                                oponentes_str = ", ".join(map(str, h['Oponentes']))
                                st.write(
                                    "Ronda " + str(h['Ronda']) + " - Mesa " + str(h['Mesa']) + ": "
                                    + str(h['Posicion']) + " (" + str(h['Puntos']) + " pts) vs " + oponentes_str
                                )
                        else:
                            st.info("No hay historial para este jugador.")
            else:
                st.info("No hay jugadores registrados.")

        # --- TAB 5: EXPORT ---
        with tab5:
            st.subheader("Exportar Resultados")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### CSV")
                csv_data = export_to_csv()
                if csv_data:
                    filename = "torneo_resultados_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
                    st.download_button(
                        label="Descargar CSV",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv"
                    )
                else:
                    st.info("No hay datos para exportar.")

            with col2:
                st.markdown("### Tabla Final")
                df = get_final_standings()
                if not df.empty:
                    df.index = range(1, len(df) + 1)
                    df.index.name = "Pos"
                    st.table(df)
                else:
                    st.info("No hay datos para mostrar.")

    else:
        # --- FINAL PODIUM ---
        st.balloons()
        st.markdown("<h1 style='text-align:center;'>RESULTADOS FINALES</h1>", unsafe_allow_html=True)

        top_3 = sorted(
            [(n, d) for n, d in st.session_state.jugadores.items()
             if n not in st.session_state.dropped_players],
            key=lambda x: (x[1]["puntos"], calculate_omw(x[0]), x[0]),
            reverse=True
        )[:3]

        c1, c2, c3 = st.columns(3)
        pos_data = [
            {"col": c2, "idx": 0, "label": "1er Puesto", "style": "gold"},
            {"col": c1, "idx": 1, "label": "2do Puesto", "style": "silver"},
            {"col": c3, "idx": 2, "label": "3er Puesto", "style": "bronze"}
        ]

        for p in pos_data:
            if len(top_3) > p["idx"]:
                n, d = top_3[p["idx"]]
                with p["col"]:
                    html = """
                        <div class='podium-card """ + p['style'] + """'>
                            <h2>""" + p['label'] + """</h2>
                            <h3 style='margin-bottom:0;'>""" + n + """</h3>
                            <div class='commander-name'>""" + str(d['comandante']) + """</div>
                            <h2 style='color:#00CC66; margin-top:5px;'>""" + str(d['puntos']) + """ Pts</h2>
                            <p>OMW%: {:.3f}</p>
                        </div>
                    """.format(calculate_omw(n))
                    st.markdown(html, unsafe_allow_html=True)

        st.divider()
        st.subheader("Tabla de Posiciones Final")
        df_f = get_final_standings()
        if not df_f.empty:
            df_f.index = range(1, len(df_f) + 1)
            df_f.index.name = "Pos"
            st.table(df_f)

        st.divider()
        if st.button("Nuevo Torneo"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.clear()
            init_session_state()
            st.rerun()

if __name__ == "__main__":
    main()
