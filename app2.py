import streamlit as st
import pandas as pd
import random
import requests
import json
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Commander Tournament Pro", page_icon="🏆", layout="wide")

# Estilos CSS corregidos
st.markdown("""
    <style>
    .podium-card { text-align: center; padding: 15px; border-radius: 15px; background-color: #1E1E1E; border: 2px solid #464855; margin-bottom: 10px; }
    .gold { border-color: #FFD700; box-shadow: 0px 0px 15px #FFD700; }
    .silver { border-color: #C0C0C0; box-shadow: 0px 0px 10px #C0C0C0; }
    .bronze { border-color: #CD7F32; box-shadow: 0px 0px 10px #CD7F32; }
    .commander-name { color: #888; font-style: italic; font-size: 0.85em; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "torneo_data.json"


# --- PERSISTENCIA ---
def guardar_datos():
    data = {
        "jugadores": st.session_state.jugadores,
        "historial": st.session_state.historial,
        "ronda_actual": st.session_state.ronda_actual,
        "puntos_config": st.session_state.puntos_config,
        "finalizado": st.session_state.finalizado,
        "mesas_activas": st.session_state.mesas_activas
    }
    with open(DB_FILE, "w") as f:
        json.dump(data, f)


def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for k, v in data.items(): st.session_state[k] = v


# --- INICIALIZACIÓN ---
if 'jugadores' not in st.session_state:
    st.session_state.update({
        "jugadores": {}, "historial": [], "ronda_actual": 1,
        "puntos_config": {"1°": 4, "2°": 3, "3°": 2, "4°": 1},
        "finalizado": False, "mesas_activas": None
    })
    cargar_datos()


# --- FUNCIONES ---
@st.cache_data(ttl=3600)
def buscar_nombres_sugeridos(query):
    if len(query) < 3: return []
    try:
        r = requests.get(f"https://api.scryfall.com/cards/autocomplete?q={query}")
        return r.json().get('data', [])
    except:
        return []


@st.cache_data(ttl=3600)
def obtener_datos_carta(nombre_exacto):
    try:
        r = requests.get(f"https://api.scryfall.com/cards/named?exact={nombre_exacto}")
        if r.status_code == 200:
            d = r.json()
            img = d['image_uris']['normal'] if 'image_uris' in d else d['card_faces'][0]['image_uris']['normal']
            return {"nombre": d['name'], "foto": img}
    except:
        return None


def calcular_omw(nombre):
    datos = st.session_state.jugadores.get(nombre)
    if not datos or not datos.get("oponentes") or datos["partidas"] == 0: return 0.0
    wrs = []
    for op_n in datos["oponentes"]:
        op = st.session_state.jugadores.get(op_n)
        if op and op.get("partidas", 0) > 0:
            wrs.append(max(op["puntos"] / (op["partidas"] * 4), 0.33))
    return sum(wrs) / len(wrs) if wrs else 0.0


# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Administración")
    es_admin = st.toggle("Modo Administrador", value=False)

    if es_admin:
        st.subheader("Configuración Global")
        for k in ["1°", "2°", "3°", "4°"]:
            st.session_state.puntos_config[k] = st.number_input(f"Pts {k}", value=st.session_state.puntos_config[k],
                                                                key=f"cfg_{k}")

        if st.button("🗑️ Resetear Torneo"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.clear()
            st.rerun()

    st.divider()
    st.subheader("📊 Standings")
    # Ordenamiento Robusto: Puntos > OMW > Nombre
    jug_sort = sorted(
        st.session_state.jugadores.items(),
        key=lambda x: (x[1]["puntos"], calcular_omw(x[0]), x[0]),
        reverse=True
    )
    for i, (n, d) in enumerate(jug_sort):
        st.write(f"{i + 1}. **{n}**: {d['puntos']} pts")

# --- INTERFAZ PRINCIPAL ---
if not st.session_state.finalizado:
    t1, t2, t3 = st.tabs(["👥 Jugadores", "⚔️ Mesas", "📜 Historial"])

    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Inscripción")
            n_j = st.text_input("Nombre del Jugador")
            b_c = st.text_input("Comandante")
            opc = buscar_nombres_sugeridos(b_c)
            c_s = st.selectbox("Carta Scryfall", opc if opc else ["..."])
            if st.button("Añadir") and n_j:
                dat = obtener_datos_carta(c_s)
                if dat:
                    st.session_state.jugadores[n_j] = {
                        "puntos": 0, "comandante": dat["nombre"], "foto": dat["foto"],
                        "oponentes": [], "partidas": 0
                    }
                    guardar_datos();
                    st.rerun()

        with c2:
            st.subheader(f"Jugadores ({len(st.session_state.jugadores)})")
            cols = st.columns(2)
            for i, (n, d) in enumerate(st.session_state.jugadores.items()):
                with cols[i % 2].container(border=True):
                    sc1, sc2 = st.columns([1, 2])
                    sc1.image(d["foto"])
                    sc2.write(f"**{n}**")
                    if es_admin:
                        st.session_state.jugadores[n]["puntos"] = sc2.number_input(f"Pts {n}", value=d["puntos"],
                                                                                   key=f"m_pts_{n}")
                    else:
                        sc2.write(f"Pts: {d['puntos']}")
                    if st.button("Borrar", key=f"del_{n}"):
                        del st.session_state.jugadores[n]
                        guardar_datos();
                        st.rerun()
            if es_admin: st.button("💾 Guardar Standings Manuales", on_click=guardar_datos)

    with t2:
        st.subheader("Gestión de Mesas")
        col_m1, col_m2 = st.columns(2)
        modo_emp = col_m1.selectbox("Emparejamiento", ["Aleatorio", "Suizo"])

        if col_m2.button("🎲 Generar / Resetear Mesas"):
            nombres = list(st.session_state.jugadores.keys())
            if modo_emp == "Suizo":
                nombres.sort(key=lambda x: (st.session_state.jugadores[x]["puntos"], calcular_omw(x)), reverse=True)
            else:
                random.shuffle(nombres)
            st.session_state.mesas_activas = [nombres[i:i + 4] for i in range(0, len(nombres), 4)]
            guardar_datos()

        if st.session_state.mesas_activas:
            # EDICIÓN DE MESAS (Solo Admin)
            if es_admin:
                with st.expander("🛠️ Editar Mesas Manualmente", expanded=True):
                    for idx, mesa in enumerate(st.session_state.mesas_activas):
                        st.session_state.mesas_activas[idx] = st.multiselect(
                            f"Mesa {idx + 1}", options=list(st.session_state.jugadores.keys()),
                            default=mesa, key=f"edit_m_{idx}"
                        )
                    if st.button("Añadir Mesa Vacía"):
                        st.session_state.mesas_activas.append([])
                        st.rerun()

            with st.form("ronda_form"):
                st.subheader(f"Resultados Ronda {st.session_state.ronda_actual}")
                ronda_results = []
                for idx, mesa in enumerate(st.session_state.mesas_activas):
                    if not mesa: continue
                    st.markdown(f"**Mesa {idx + 1}**")
                    m_cols = st.columns(len(mesa))
                    res_m = {}
                    for i, j in enumerate(mesa):
                        with m_cols[i]:
                            st.caption(j)
                            res_m[j] = st.selectbox("Posición", [1, 2, 3, 4], key=f"r_{idx}_{j}")
                    ronda_results.append({"mesa": mesa, "posiciones": res_m})

                if st.form_submit_button("✅ Finalizar y Sumar Puntos"):
                    for m in ronda_results:
                        for jug, pos in m["posiciones"].items():
                            st.session_state.jugadores[jug]["puntos"] += st.session_state.puntos_config[f"{pos}°"]
                            st.session_state.jugadores[jug]["partidas"] += 1
                            st.session_state.jugadores[jug]["oponentes"].extend([o for o in m["mesa"] if o != jug])
                    st.session_state.historial.append(ronda_results)
                    st.session_state.ronda_actual += 1
                    st.session_state.mesas_activas = None
                    guardar_datos();
                    st.rerun()

    with t3:
        st.subheader("Historial")
        for i, ronda in enumerate(st.session_state.historial):
            with st.expander(f"Ronda {i + 1}"):
                h_table = []
                for m_idx, m_data in enumerate(ronda):
                    for jug, pos in m_data["posiciones"].items():
                        h_table.append({"Mesa": m_idx + 1, "Jugador": jug, "Lugar": f"{pos}°",
                                        "Pts+": st.session_state.puntos_config[f"{pos}°"]})
                st.table(h_table)

        st.divider()
        if st.button("🏁 FINALIZAR TODO EL TORNEO", type="primary", use_container_width=True):
            st.session_state.finalizado = True
            guardar_datos();
            st.rerun()

else:
    # --- PODIO FINAL ---
    st.balloons()
    st.markdown("<h1 style='text-align:center;'>🏆 RESULTADOS FINALES</h1>", unsafe_allow_html=True)

    top_3 = sorted(
        st.session_state.jugadores.items(),
        key=lambda x: (x[1]["puntos"], calcular_omw(x[0]), x[0]),
        reverse=True
    )[:3]

    c1, c2, c3 = st.columns(3)
    pos_data = [
        {"col": c2, "idx": 0, "label": "🥇 1er Puesto", "style": "gold"},
        {"col": c1, "idx": 1, "label": "🥈 2do Puesto", "style": "silver"},
        {"col": c3, "idx": 2, "label": "🥉 3er Puesto", "style": "bronze"}
    ]

    for p in pos_data:
        if len(top_3) > p["idx"]:
            n, d = top_3[p["idx"]]
            with p["col"]:
                st.markdown(f"""
                    <div class='podium-card {p['style']}'>
                        <h2>{p['label']}</h2>
                        <img src='{d['foto']}' style='width:100%; border-radius:10px;'>
                        <h3 style='margin-bottom:0;'>{n}</h3>
                        <div class='commander-name'>{d['comandante']}</div>
                        <h2 style='color:#00CC66; margin-top:5px;'>{d['puntos']} Pts</h2>
                    </div>
                """, unsafe_allow_html=True)

    if st.button("🔄 Nuevo Torneo"):
        if os.remove(DB_FILE): pass
        st.session_state.clear()
        st.rerun()
        