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


# --- CÁLCULO DE OMW% (INTERNO PARA DESEMPATE) ---
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

    st.write("Asignar resultados individuales:")
    puntos_dict = {
        "1° Lugar (4 pts)": 4,
        "2° Lugar (3 pts)": 3,
        "3° Lugar (2 pts)": 2,
        "4° Lugar (1 pt)": 1
    }

    res_mesa = {}
    # Usamos el número de jugadores para crear las columnas
    cols = st.columns(len(mesa))

    for i, jugador in enumerate(mesa):
        with cols[i]:
            # CAMBIO AQUÍ: Usamos el nombre del jugador en el label para que no haya pérdida
            pos = st.selectbox(
                f"Resultado: {jugador}",
                list(puntos_dict.keys()),
                key=f"res_{jugador}_{st.session_state.ronda_actual}"
            )
            res_mesa[jugador] = puntos_dict[pos]
    return res_mesa


# --- SIDEBAR (CONFIGURACIÓN Y STANDINGS) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    modo_juego = st.radio("Modo de Emparejamiento", ["Aleatorio", "Suizo"])

    st.divider()
    st.subheader("📊 Standings")

    if st.session_state.jugadores:
        # Definimos la prioridad de ordenamiento:
        # Si tiene puesto manual (1, 2, 3...), se le asigna un valor muy alto (1000 - puesto)
        # para que al usar reverse=True quede en el tope.
        def prioridad_sort(item):
            nombre, datos = item
            pos_manual = datos.get("posicion_manual", 0)
            if pos_manual > 0:
                return (1000 - pos_manual, 0)  # Prioridad máxima manual
            # Si no hay manual, usa Puntos y luego OMW%
            return (datos["puntos"], calcular_omw(nombre))


        # Ordenamos a los jugadores
        jugadores_ordenados = sorted(
            st.session_state.jugadores.items(),
            key=prioridad_sort,
            reverse=True
        )

        # Preparamos los datos para la tabla (mostrando solo lo necesario)
        datos_tabla = [{"Jugador": k, "Pts": v["puntos"]} for k, v in jugadores_ordenados]
        df_realtime = pd.DataFrame(datos_tabla)
        df_realtime.index = range(1, len(df_realtime) + 1)  # Posiciones desde 1
        st.table(df_realtime)
    else:
        st.write("Esperando inscripciones...")

# --- INTERFAZ PRINCIPAL ---
st.title("🏆 MTG Commander Tournament Manager")

if not st.session_state.finalizado:
    t1, t2, t3 = st.tabs(["📝 Inscripción", "⚔️ Rondas", "📜 Historial"])

    with t1:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1.5, 1])
            nombre_j = c1.text_input("Nombre del Jugador")
            busq = c2.text_input("Buscar Comandante...")
            opciones = buscar_nombres_sugeridos(busq)
            carta_sel = c2.selectbox("Selecciona la carta:", opciones if opciones else ["Escribe para buscar..."])
            link_m = c3.text_input("Link de Moxfield")

            if st.button("➕ Inscribir Jugador", use_container_width=True):
                if nombre_j and carta_sel not in ["Sin resultados", "Escribe para buscar..."]:
                    datos_c = obtener_datos_carta(carta_sel)
                    if datos_c:
                        st.session_state.jugadores[nombre_j] = {
                            "puntos": 0,
                            "oponentes": [],
                            "partidas": 0,
                            "comandante": datos_c["nombre"],
                            "moxfield": link_m,
                            "foto": datos_c["foto"],
                            "posicion_manual": 0
                        }
                        st.success(f"¡{nombre_j} inscrito!")
                        st.rerun()

        st.divider()
        if st.session_state.jugadores:
            st.subheader(f"👥 Jugadores Inscritos ({len(st.session_state.jugadores)})")
            cols_i = st.columns(4)
            # Creamos una lista de nombres para evitar errores de mutación al borrar
            nombres_jugadores = list(st.session_state.jugadores.keys())

            for idx, n in enumerate(nombres_jugadores):
                d = st.session_state.jugadores[n]
                with cols_i[idx % 4]:
                    with st.container(border=True):
                        if d["foto"]:
                            st.image(d["foto"], use_container_width=True)
                        st.write(f"**{n}**")

                        # Columna para botones de acción
                        c_deck, c_del = st.columns([3, 1])
                        if d["moxfield"]:
                            c_deck.link_button("📂 Deck", d["moxfield"], use_container_width=True)

                        # BOTÓN PARA ELIMINAR JUGADOR
                        if c_del.button("🗑️", key=f"del_{n}", help=f"Eliminar a {n}"):
                            del st.session_state.jugadores[n]
                            st.rerun()  # Recargamos para actualizar la lista y el contador

    with t2:
        if len(st.session_state.jugadores) < 3:
            st.info("Inscribe jugadores.")
        else:
            if st.button("🚀 Lanzar Nueva Ronda"):
                nombres = list(st.session_state.jugadores.keys())
                if modo_juego == "Suizo" and st.session_state.ronda_actual > 1:
                    nombres.sort(key=lambda x: (st.session_state.jugadores[x]["puntos"], calcular_omw(x)), reverse=True)
                else:
                    random.shuffle(nombres)

                num_jug = len(nombres)
                mesas = []
                # Lógica para 6 jugadores -> 2 mesas de 3
                if num_jug == 6:
                    mesas = [nombres[0:3], nombres[3:6]]
                else:
                    for i in range(0, num_jug, 4):
                        grupo = nombres[i:i + 4]
                        if len(grupo) <= 2 and len(mesas) > 0:
                            mesas[-1].extend(grupo)
                        else:
                            mesas.append(grupo)
                st.session_state.mesas_activas = mesas

            if st.session_state.mesas_activas:
                with st.form(f"ronda_form_{st.session_state.ronda_actual}"):
                    res_ronda = []
                    for midx, mesa in enumerate(st.session_state.mesas_activas):
                        puntos_asignados = renderizar_mesa_visual(midx + 1, mesa)
                        res_ronda.append({"mesa": mesa, "resultados": puntos_asignados})

                    if st.form_submit_button("✅ Guardar Ronda"):
                        for r in res_ronda:
                            for jugador, pts in r["resultados"].items():
                                st.session_state.jugadores[jugador]["puntos"] += pts
                                st.session_state.jugadores[jugador]["partidas"] += 1
                                st.session_state.jugadores[jugador]["oponentes"].extend(
                                    [o for o in r["mesa"] if o != jugador])

                        st.session_state.historial.append(res_ronda)
                        st.session_state.ronda_actual += 1
                        st.session_state.mesas_activas = None
                        st.rerun()

    with t3:
        st.subheader("🏆 Ajuste de Ranking Final")
        st.write("Si el torneo terminó y necesitas ajustar el orden por dados o acuerdo, hazlo aquí:")

        with st.expander("📝 Editar Orden de la Tabla"):
            with st.form("editor_ranking"):
                cambios_pos = {}
                # Mostramos a los jugadores para asignarles su puesto final
                for nombre, datos in st.session_state.jugadores.items():
                    col_n, col_p = st.columns([2, 1])
                    with col_n:
                        st.write(f"**{nombre}** ({datos['puntos']} pts)")
                    with col_p:
                        # Si es 0, el programa usará la lógica normal (Pts > OMW)
                        nueva_pos = st.number_input(f"Puesto para {nombre}", min_value=0,
                                                    value=int(datos.get("posicion_manual", 0)), key=f"rank_{nombre}")
                    cambios_pos[nombre] = nueva_pos

                if st.form_submit_button("💾 Confirmar Posiciones"):
                    for n, p in cambios_pos.items():
                        st.session_state.jugadores[n]["posicion_manual"] = p
                    st.success("¡Ranking ajustado! Revisa el podio al finalizar.")
                    st.rerun()

        st.divider()
        st.subheader("📜 Historial de Rondas")
        for i, ron in enumerate(st.session_state.historial):
            with st.expander(f"Ronda {i + 1}"):
                datos_h = []
                for m_idx, m_data in enumerate(ron):
                    mesa_txt = " | ".join(m_data['mesa'])
                    fila = {"Mesa": f"Mesa {m_idx + 1}: {mesa_txt}"}
                    for jug, pts in m_data['resultados'].items():
                        fila[jug] = f"{pts} pts"
                    datos_h.append(fila)
                st.table(pd.DataFrame(datos_h).fillna("-"))

    if st.button("🏁 FINALIZAR"):
        st.session_state.finalizado = True
        st.rerun()

else:
    st.balloons()


    # Lógica de ordenamiento consistente
    def prioridad_sort(item):
        nombre, datos = item
        pos_manual = datos.get("posicion_manual", 0)
        if pos_manual > 0:
            return (1000 - pos_manual, 0)
        return (datos["puntos"], calcular_omw(nombre))


    sorted_players = sorted(
        st.session_state.jugadores.items(),
        key=prioridad_sort,
        reverse=True
    )

    top_3 = sorted_players[:3]
    st.markdown("<h1 style='text-align:center;'>🏆 PODIO FINAL</h1>", unsafe_allow_html=True)

    # Proporción de columnas: el centro es 1.5 veces más grande
    cols_podio = st.columns([1, 1.5, 1])

    # --- RENDERIZADO MANUAL POR POSICIÓN ---

    # 🥇 1er PUESTO (CENTRO - Índice 0 de top_3)
    if len(top_3) >= 1:
        with cols_podio[1]:
            nombre, datos = top_3[0]
            st.markdown("<h2 style='text-align:center; color:#FFD700;'>🥇 1er Puesto</h2>", unsafe_allow_html=True)
            if datos["foto"]:
                st.image(datos["foto"], use_container_width=True)
            st.markdown(f"<p style='text-align:center; font-size:20px;'><b>{nombre}</b><br>{datos['comandante']}</p>",
                        unsafe_allow_html=True)

    # 🥈 2do PUESTO (IZQUIERDA - Índice 1 de top_3)
    if len(top_3) >= 2:
        with cols_podio[0]:
            nombre, datos = top_3[1]
            st.markdown("<h3 style='text-align:center; color:#C0C0C0;'>🥈 2do Puesto</h3>", unsafe_allow_html=True)
            if datos["foto"]:
                st.image(datos["foto"], use_container_width=True)
            st.markdown(f"<p style='text-align:center;'><b>{nombre}</b><br>{datos['comandante']}</p>",
                        unsafe_allow_html=True)

    # 🥉 3er PUESTO (DERECHA - Índice 2 de top_3)
    if len(top_3) >= 3:
        with cols_podio[2]:
            nombre, datos = top_3[2]
            st.markdown("<h3 style='text-align:center; color:#CD7F32;'>🥉 3er Puesto</h3>", unsafe_allow_html=True)
            if datos["foto"]:
                st.image(datos["foto"], use_container_width=True)
            st.markdown(f"<p style='text-align:center;'><b>{nombre}</b><br>{datos['comandante']}</p>",
                        unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 Clasificación Final")
    df_final = pd.DataFrame([{"Jugador": n, "Pts": d["puntos"]} for n, d in sorted_players])
    df_final.index = range(1, len(df_final) + 1)
    st.table(df_final)

    if st.button("🔄 Comenzar Nuevo Torneo", use_container_width=True):
        st.session_state.clear()
        st.rerun()