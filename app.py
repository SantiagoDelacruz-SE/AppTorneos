import streamlit as st
import pandas as pd
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Commander Tournament Pro", page_icon="🎴", layout="wide")

# --- INICIALIZACIÓN DE ESTADO (Session State) ---
if 'jugadores' not in st.session_state:
    # {nombre: {"puntos": 0, "oponentes": [], "partidas": 0}}
    st.session_state.jugadores = {}
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'ronda_actual' not in st.session_state:
    st.session_state.ronda_actual = 1
if 'mesas_activas' not in st.session_state:
    st.session_state.mesas_activas = None
if 'finalizado' not in st.session_state:
    st.session_state.finalizado = False


# --- FUNCIONES LÓGICAS Y DESEMPATE ---

def calcular_omw(nombre):
    datos = st.session_state.jugadores.get(nombre)
    if not datos or not datos["oponentes"] or datos["partidas"] == 0:
        return 0.0

    wr_oponentes = []
    for op_nombre in datos["oponentes"]:
        op = st.session_state.jugadores[op_nombre]
        max_puntos = op["partidas"] * 4
        wr = (op["puntos"] / max_puntos) if max_puntos > 0 else 0
        wr_oponentes.append(max(wr, 0.33))  # Regla competitiva 33%

    return sum(wr_oponentes) / len(wr_oponentes)


def generar_emparejamientos(modo):
    nombres = list(st.session_state.jugadores.keys())
    if modo == "Suizo":
        # Ordenar por Puntos desc, luego por OMW% desc
        nombres.sort(key=lambda x: (st.session_state.jugadores[x]["puntos"], calcular_omw(x)), reverse=True)
    else:
        random.shuffle(nombres)

    n = len(nombres)
    mesas = []
    i = 0
    while i < n:
        restantes = n - i
        if restantes == 6:
            tam = 3
        elif restantes == 5:
            tam = 3
        elif restantes >= 4:
            tam = 4
        else:
            tam = restantes

        mesas.append(nombres[i:i + tam])
        i += tam
    return mesas


def registrar_jugador_callback():
    nombre = st.session_state.temp_nombre.strip()
    if nombre and nombre not in st.session_state.jugadores:
        st.session_state.jugadores[nombre] = {"puntos": 0, "oponentes": [], "partidas": 0}
        st.session_state.temp_nombre = ""
    elif nombre in st.session_state.jugadores:
        st.error(f"El jugador '{nombre}' ya está inscrito.")


# --- COMPONENTE VISUAL DE LA MESA ---

def renderizar_mesa_visual(num_mesa, mesa):
    st.markdown(f"#### 🎴 Mesa {num_mesa}")

    p1 = mesa[0]
    p2 = mesa[1] if len(mesa) > 1 else "-"
    p3 = mesa[2] if len(mesa) > 2 else "-"
    p4 = mesa[3] if len(mesa) > 3 else "-"

    with st.container(border=True):
        # Fila Superior: Pos 2 y Pos 3
        col_t1, col_t2, col_t3 = st.columns([2, 1, 2])
        with col_t1:
            st.markdown(f"<div style='text-align: right; color: #00CC66;'><b>Inicia : {p1}</b></div>", unsafe_allow_html=True)
        with col_t3:
            st.markdown(f"<div style='text-align: left;'><b>Asiento 2 : {p3}</b></div>", unsafe_allow_html=True)

        # Fila Central: El Tablero
        col_m1, col_m2, col_m3 = st.columns([2, 1, 2])
        with col_m2:
            st.markdown("""
                <div style="height: 60px; border: 2px solid white; border-radius: 10px; 
                            display: flex; align-items: center; justify-content: center; 
                            background-color: #1e1e1e; margin: 5px 0;">
                    <b style="color: white; font-size: 12px;">MTG</b>
                </div>
            """, unsafe_allow_html=True)

        # Fila Inferior: Pos 1 (Inicia) y Pos 4
        col_b1, col_b2, col_b3 = st.columns([2, 1, 2])
        with col_b1:
            st.markdown(f"<div style='text-align: right;'><b>Asiento 3 : {p2}</b></div>",
                        unsafe_allow_html=True)
        with col_b3:
            st.markdown(f"<div style='text-align: left;'><b>Asiento 4: {p4}</b></div>", unsafe_allow_html=True)

    # Inputs de resultados (dentro del formulario)
    st.write("Selecciona posiciones finales:")
    c1, c2, c3, c4 = st.columns(4)
    with c1: r1 = st.selectbox("1° (4 pts)", [None] + mesa, key=f"m{num_mesa}_r1")
    with c2: r2 = st.selectbox("2° (3 pts)", [None] + mesa, key=f"m{num_mesa}_r2")
    with c3: r3 = st.selectbox("3° (2 pts)", [None] + mesa, key=f"m{num_mesa}_r3")
    with c4:
        r4 = st.selectbox("4° (1 pt)", [None] + mesa, key=f"m{num_mesa}_r4") if len(mesa) == 4 else None

    return [r1, r2, r3, r4] if r4 else [r1, r2, r3]


# --- INTERFAZ SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    modo_juego = st.radio("Modo de Emparejamiento", ["Aleatorio", "Suizo"])

    st.divider()
    st.subheader("📊 Standings Actuales")
    if st.session_state.jugadores:
        datos_tabla = []
        for nom, stats in st.session_state.jugadores.items():
            datos_tabla.append({
                "Jugador": nom,
                "Puntos": stats["puntos"],
                "OMW%": f"{calcular_omw(nom):.3f}"
            })
        df = pd.DataFrame(datos_tabla).sort_values(by=["Puntos", "OMW%"], ascending=False)
        df.index = range(1, len(df) + 1)
        df.index.name = "Pos"
        st.table(df)
    else:
        st.write("Sin jugadores.")

# --- CUERPO PRINCIPAL ---
st.title("🏆 MTG Commander Tournament Manager")

if not st.session_state.finalizado:
    tab1, tab2, tab3 = st.tabs(["📝 Inscripciones", "⚔️ Gestión de Rondas", "📜 Historial"])

    with tab1:
        st.subheader("Registro de Jugadores")
        st.text_input("Nombre y presiona Enter:", key="temp_nombre", on_change=registrar_jugador_callback)
        st.write(f"Jugadores inscritos: **{len(st.session_state.jugadores)}**")
        if st.session_state.jugadores:
            st.info(", ".join(st.session_state.jugadores.keys()))

    with tab2:
        if len(st.session_state.jugadores) < 3:
            st.warning("Se requieren al menos 3 jugadores.")
        else:
            if st.button("🚀 Generar Nueva Ronda"):
                st.session_state.mesas_activas = generar_emparejamientos(modo_juego)

            if st.session_state.mesas_activas:
                st.subheader(f"Ronda {st.session_state.ronda_actual}")

                # FORMULARIO ÚNICO PARA TODA LA RONDA
                with st.form(key=f"form_ronda_{st.session_state.ronda_actual}"):
                    resultados_acumulados = []
                    for idx, mesa in enumerate(st.session_state.mesas_activas):
                        podio = renderizar_mesa_visual(idx + 1, mesa)
                        resultados_acumulados.append({"mesa": mesa, "podio": podio})
                        st.divider()

                    if st.form_submit_button("✅ Finalizar Ronda y Guardar Puntos"):
                        # Validar duplicados o nulos
                        error = False
                        for res in resultados_acumulados:
                            if None in res["podio"] or len(set(res["podio"])) != len(res["podio"]):
                                error = True

                        if error:
                            st.error(
                                "Error: Revisa que todos los puestos estén llenos y no haya jugadores repetidos en la misma mesa.")
                        else:
                            pts_map = [4, 3, 2, 1]
                            for res in resultados_acumulados:
                                m = res["mesa"]
                                # Actualizar stats de oponentes y partidas
                                for j in m:
                                    st.session_state.jugadores[j]["partidas"] += 1
                                    rivales = [r for r in m if r != j]
                                    st.session_state.jugadores[j]["oponentes"].extend(rivales)
                                # Sumar puntos por podio
                                for i, player in enumerate(res["podio"]):
                                    st.session_state.jugadores[player]["puntos"] += pts_map[i]

                            st.session_state.historial.append(resultados_acumulados)
                            st.session_state.ronda_actual += 1
                            st.session_state.mesas_activas = None
                            st.rerun()

            st.divider()
            if st.button("🏁 FINALIZAR TORNEO"):
                st.session_state.finalizado = True
                st.rerun()

    with tab3:
        for i, r in enumerate(st.session_state.historial):
            with st.expander(f"Ronda {i + 1} - Ver Enfrentamientos"):
                for m_idx, mesa_data in enumerate(r):
                    st.write(f"**Mesa {m_idx + 1}:** {', '.join(mesa_data['mesa'])}")
                    st.write(f"Resultados: 1° {mesa_data['podio'][0]} | 2° {mesa_data['podio'][1]}...")

# --- PANTALLA FINAL DE GANADOR ---
else:
    st.balloons()
    ganador = max(st.session_state.jugadores, key=lambda x: (st.session_state.jugadores[x]["puntos"], calcular_omw(x)))

    st.markdown(f"""
        <div style="text-align:center; padding: 50px;">
            <h1 style="font-size: 100px;">🏆</h1>
            <h1 style="color: #FFD700;">¡EL CAMPEÓN ES {ganador.upper()}!</h1>
            <p>Torneo finalizado con éxito.</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Tabla de Posiciones Final")
    data_final = []
    for nom, stats in st.session_state.jugadores.items():
        data_final.append({"Jugador": nom, "Puntos": stats["puntos"], "OMW%": f"{calcular_omw(nom):.3f}"})

    df_f = pd.DataFrame(data_final).sort_values(by=["Puntos", "OMW%"], ascending=False)
    df_f.index = range(1, len(df_f) + 1)
    df_f.index.name = "Pos"
    st.table(df_f)

    if st.button("🔄 Comenzar Nuevo Torneo"):
        st.session_state.clear()
        st.rerun()