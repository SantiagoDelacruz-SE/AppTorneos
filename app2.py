import streamlit as st
import pandas as pd
import random
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Commander Tournament Pro", page_icon="🎴", layout="wide")


# --- FUNCIONES DE SCRYFALL ---
def buscar_nombres_sugeridos(query):
    if len(query) < 3: return []
    try:
        response = requests.get(f"https://api.scryfall.com/cards/autocomplete?q={query}")
        if response.status_code == 200:
            return response.json().get('data', [])
    except:
        return []
    return []


def obtener_datos_carta(nombre_exacto):
    try:
        response = requests.get(f"https://api.scryfall.com/cards/named?exact={nombre_exacto}")
        if response.status_code == 200:
            data = response.json()
            img = data['image_uris']['normal'] if 'image_uris' in data else data['card_faces'][0]['image_uris'][
                'normal']
            return {"nombre": data['name'], "foto": img}
    except:
        return None
    return None


# --- INICIALIZACIÓN DE ESTADO ---
if 'jugadores' not in st.session_state:
    st.session_state.jugadores = {}
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'ronda_actual' not in st.session_state:
    st.session_state.ronda_actual = 1
if 'mesas_activas' not in st.session_state:
    st.session_state.mesas_activas = None
if 'finalizado' not in st.session_state:
    st.session_state.finalizado = False


# --- CÁLCULO DE OMW% (INTERNO) ---
def calcular_omw(nombre):
    datos = st.session_state.jugadores.get(nombre)
    if not datos or not datos["oponentes"] or datos["partidas"] == 0: return 0.0
    wrs = []
    for op_n in datos["oponentes"]:
        op = st.session_state.jugadores[op_n]
        wr = (op["puntos"] / (op["partidas"] * 4)) if op["partidas"] > 0 else 0
        wrs.append(max(wr, 0.33))
    return sum(wrs) / len(wrs)


# --- COMPONENTE MESA (DISEÑO SOLICITADO) ---
def renderizar_mesa_visual(num_mesa, mesa):
    st.markdown(f"### 🎴 Mesa {num_mesa}")
    j1_inicia = mesa[0]
    j2 = mesa[1] if len(mesa) > 1 else "-"
    j3 = mesa[2] if len(mesa) > 2 else "-"
    j4 = mesa[3] if len(mesa) > 3 else "-"

    with st.container(border=True):
        col_izq, col_mtg, col_der = st.columns([2, 1, 2])
        with col_izq:
            st.markdown(f"<div style='text-align: right; margin-bottom: 20px;'><b>{j2}</b></div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: right; color: #00CC66;'><b>Inicia: {j1_inicia}</b></div>",
                        unsafe_allow_html=True)
        with col_mtg:
            st.markdown(
                '<div style="height: 100px; border: 2px solid white; border-radius: 10px; display: flex; align-items: center; justify-content: center; background-color: #1e1e1e; margin: auto; width: 50px;"><b style="color: white; font-size: 10px;">MTG</b></div>',
                unsafe_allow_html=True)
        with col_der:
            st.markdown(f"<div style='text-align: left; margin-bottom: 20px;'><b>{j3}</b></div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: left;'><b>{j4}</b></div>", unsafe_allow_html=True)

    st.write("Selecciona posiciones finales:")
    cols = st.columns(len(mesa))
    res = []
    for i in range(len(mesa)):
        with cols[i]:
            sel = st.selectbox(f"{i + 1}° Lugar", [None] + mesa, key=f"m{num_mesa}_{i}_{st.session_state.ronda_actual}")
            res.append(sel)
    return res


# --- SIDEBAR (MODO Y STANDINGS) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    modo_juego = st.radio("Modo de Emparejamiento", ["Aleatorio", "Suizo"])

    st.divider()
    st.subheader("📊 Standings")
    if st.session_state.jugadores:
        datos_tabla = [{"Jugador": k, "Pts": v["puntos"]} for k, v in st.session_state.jugadores.items()]
        df_realtime = pd.DataFrame(datos_tabla).sort_values(
            by=["Pts"],
            key=lambda x: [(st.session_state.jugadores[n]["puntos"], calcular_omw(n)) for n in
                           st.session_state.jugadores],
            ascending=False
        )
        df_realtime.index = range(1, len(df_realtime) + 1)
        st.table(df_realtime)

# --- INTERFAZ PRINCIPAL ---
st.title("🏆 MTG Commander Tournament Manager")

if not st.session_state.finalizado:
    t1, t2, t3 = st.tabs(["📝 Inscripción", "⚔️ Rondas", "📜 Historial"])

    with t1:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1.5, 1])
            nombre_j = c1.text_input("Nombre del Jugador", key="ins_nom")
            busq = c2.text_input("Buscar Comandante...", key="ins_busq")
            opciones = buscar_nombres_sugeridos(busq)
            carta_sel = c2.selectbox("Selecciona la carta:", opciones if opciones else ["Escribe para buscar..."],
                                     key="ins_sel")
            link_m = c3.text_input("Link de Moxfield", key="ins_link")

            if st.button("➕ Inscribir Jugador", use_container_width=True):
                if nombre_j and carta_sel not in ["Sin resultados", "Escribe para buscar..."]:
                    datos_c = obtener_datos_carta(carta_sel)
                    if datos_c:
                        st.session_state.jugadores[nombre_j] = {
                            "puntos": 0, "oponentes": [], "partidas": 0,
                            "comandante": datos_c["nombre"], "moxfield": link_m, "foto": datos_c["foto"]
                        }
                        st.rerun()

        st.divider()
        if st.session_state.jugadores:
            cols_i = st.columns(4)
            for idx, (n, d) in enumerate(st.session_state.jugadores.items()):
                with cols_i[idx % 4]:
                    with st.container(border=True):
                        if d["foto"]: st.image(d["foto"], use_container_width=True)
                        st.write(f"**{n}**")
                        if d["moxfield"]: st.link_button("📂 Deck", d["moxfield"], use_container_width=True)

    with t2:
        if len(st.session_state.jugadores) < 3:
            st.info("Inscribe jugadores.")
        else:
            if st.button("🚀 Lanzar Nueva Ronda"):
                nombres = list(st.session_state.jugadores.keys())

                # Ordenar para Suizo o Aleatorio
                if modo_juego == "Suizo" and st.session_state.ronda_actual > 1:
                    nombres.sort(key=lambda x: (st.session_state.jugadores[x]["puntos"], calcular_omw(x)), reverse=True)
                else:
                    random.shuffle(nombres)

                num_jugadores = len(nombres)
                mesas = []

                # --- LÓGICA DE REPARTO INTELIGENTE ---
                if num_jugadores == 6:
                    # Caso específico: 2 mesas de 3
                    mesas.append(nombres[0:3])
                    mesas.append(nombres[3:6])
                elif num_jugadores == 5:
                    # Caso específico: 1 mesa de 5 (o puedes dividir 3 y 2, pero 2 es poco para EDH)
                    mesas.append(nombres)
                else:
                    # Lógica general (Mesas de 4, restos se unen a la última)
                    for i in range(0, num_jugadores, 4):
                        grupo = nombres[i:i + 4]
                        if len(grupo) == 2 and len(mesas) > 0:
                            mesas[-1].extend(grupo)  # Si sobran 2, se unen a la mesa de 4 (Mesa de 6)
                        elif len(grupo) == 1 and len(mesas) > 0:
                            mesas[-1].extend(grupo)  # Si sobra 1, se une (Mesa de 5)
                        else:
                            mesas.append(grupo)

                st.session_state.mesas_activas = mesas

            if st.session_state.mesas_activas:
                with st.form(f"ronda_{st.session_state.ronda_actual}"):
                    res_ronda = []
                    for midx, mesa in enumerate(st.session_state.mesas_activas):
                        podio = renderizar_mesa_visual(midx + 1, mesa)
                        res_ronda.append({"mesa": mesa, "podio": podio})

                    if st.form_submit_button("✅ Guardar Resultados de la Ronda"):
                        error_encontrado = False
                        for r in res_ronda:
                            seleccionados = [n for n in r["podio"] if n is not None]
                            if len(seleccionados) != len(set(seleccionados)) or len(seleccionados) != len(r["mesa"]):
                                error_encontrado = True
                                break

                        if error_encontrado:
                            st.error("Error: Revisa que todos los puestos estén llenos y no haya repetidos.")
                        else:
                            pts_esq = [4, 3, 2, 1]
                            for r in res_ronda:
                                for p_m in r["mesa"]:
                                    st.session_state.jugadores[p_m]["partidas"] += 1
                                    st.session_state.jugadores[p_m]["oponentes"].extend(
                                        [o for o in r["mesa"] if o != p_m])
                                for i, gan in enumerate(r["podio"]):
                                    if gan: st.session_state.jugadores[gan]["puntos"] += pts_esq[i]
                            st.session_state.historial.append(res_ronda)
                            st.session_state.ronda_actual += 1
                            st.session_state.mesas_activas = None
                            st.rerun()

    with t3:
        st.subheader("Historial Detallado de Rondas")
        for i, ron in enumerate(st.session_state.historial):
            with st.expander(f"Ronda {i + 1}"):
                # Crear tabla para el historial de esta ronda
                datos_historial = []
                for m_idx, m_data in enumerate(ron):
                    mesa_str = " | ".join(m_data['mesa'])
                    posiciones = {}
                    pts_esq = [4, 3, 2, 1]
                    for pos_idx, player in enumerate(m_data['podio']):
                        posiciones[f"{pos_idx + 1}° Lugar"] = f"{player} ({pts_esq[pos_idx]} pts)"

                    fila = {"Mesa": f"Mesa {m_idx + 1}: {mesa_str}"}
                    fila.update(posiciones)
                    datos_historial.append(fila)

                st.table(pd.DataFrame(datos_historial))

    if st.button("🏁 FINALIZAR TORNEO"):
        st.session_state.finalizado = True
        st.rerun()

else:
    st.balloons()
    sorted_players = sorted(st.session_state.jugadores.items(), key=lambda x: (x[1]["puntos"], calcular_omw(x[0])),
                            reverse=True)
    top_3 = sorted_players[:3]
    st.markdown("<h1 style='text-align:center;'>🏆 PODIO FINAL</h1>", unsafe_allow_html=True)
    c_p = st.columns([1, 1.2, 1])
    for i, label, color in [(1, "🥈 2do Puesto", "#C0C0C0"), (0, "🥇 1er Puesto", "#FFD700"),
                            (2, "🥉 3er Puesto", "#CD7F32")]:
        if len(top_3) > i:
            with c_p[i]:
                st.markdown(f"<h3 style='text-align:center; color:{color};'>{label}</h3>", unsafe_allow_html=True)
                st.image(top_3[i][1]["foto"], use_container_width=True)
                st.markdown(f"<p style='text-align:center;'><b>{top_3[i][0]}</b><br>{top_3[i][1]['comandante']}</p>",
                            unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 Clasificación Final")
    df_f = pd.DataFrame([{"Jugador": n, "Pts": d["puntos"]} for n, d in sorted_players])
    df_f.index = range(1, len(df_f) + 1)
    st.table(df_f)

    if st.button("🔄 Nuevo Torneo"): st.session_state.clear(); st.rerun()