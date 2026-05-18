"""
client_finder — Interface Web
Execute com: streamlit run app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from client_finder.search import search as do_search, search_demo
from client_finder.config import DEFAULT_RADIUS_KM

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Client Finder",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏢 Client Finder")
    st.caption("Empresas de médio e grande porte por raio geográfico")
    st.divider()

    endereco = st.text_input(
        "Endereço central",
        placeholder="Ex: Av. Paulista, 1000, São Paulo, SP",
    )

    raio = st.slider("Raio de busca (km)", min_value=1, max_value=20, value=5, step=1)

    modo = st.radio(
        "Fonte de dados",
        options=["Demo (sem internet)", "Quick (OpenStreetMap)", "Full (Receita Federal)"],
        index=0,
    )

    limite = st.number_input("Máx. resultados", min_value=10, max_value=1000, value=100, step=10)

    buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)

    st.divider()
    st.caption("**Modos:**")
    st.caption("• **Demo** – dados fictícios para testar a tela")
    st.caption("• **Quick** – OpenStreetMap (sem setup, parcial)")
    st.caption("• **Full** – Receita Federal local (requer `import`)")


# ─── Main area ───────────────────────────────────────────────────────────────
st.header("Empresas de Médio e Grande Porte")

if not buscar or not endereco:
    st.info("Informe um endereço na barra lateral e clique em **Buscar**.")
    st.stop()

# ─── Run search ──────────────────────────────────────────────────────────────
with st.spinner("Buscando empresas..."):
    try:
        if "Demo" in modo:
            result = search_demo(endereco, radius_km=raio)
            st.warning("Modo DEMO — dados fictícios para validação da interface.")
        elif "Quick" in modo:
            result = do_search(endereco, radius_km=raio, mode="quick", limit=limite, verbose=False)
        else:
            result = do_search(endereco, radius_km=raio, mode="full", limit=limite, verbose=False)
    except ValueError as e:
        st.error(f"Endereço não encontrado: {e}")
        st.stop()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

if result.total == 0:
    st.warning("Nenhuma empresa encontrada. Tente aumentar o raio ou mudar o modo.")
    st.stop()

# ─── Metrics ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Empresas encontradas", result.total)
col2.metric("Raio buscado", f"{raio} km")
col3.metric("Mais próxima", f"{min(e.distancia_km or 0 for e in result.empresas):.2f} km")
col4.metric("Mais distante", f"{max(e.distancia_km or 0 for e in result.empresas):.2f} km")

st.divider()

# ─── Layout: tabela + mapa ────────────────────────────────────────────────────
tab_tabela, tab_mapa = st.tabs(["📋 Tabela", "🗺️ Mapa"])

# ── Tabela ────────────────────────────────────────────────────────────────────
with tab_tabela:
    rows = []
    for e in result.empresas:
        cnpj = e.cnpj.zfill(14)
        cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}" \
                   if e.cnpj != "00000000000000" else "N/D"
        rows.append({
            "CNPJ": cnpj_fmt,
            "Razão Social": e.razao_social,
            "Nome Fantasia": e.nome_fantasia or "",
            "Porte": e.porte_desc,
            "Logradouro": f"{e.logradouro}, {e.numero}".strip(", "),
            "Bairro": e.bairro or "",
            "Município": e.municipio or "",
            "UF": e.uf or "",
            "CEP": e.cep or "",
            "Telefone": e.telefone or "",
            "Email": e.email or "",
            "Dist (km)": e.distancia_km,
        })

    df = pd.DataFrame(rows)

    # filters
    with st.expander("Filtros", expanded=False):
        fc1, fc2 = st.columns(2)
        uf_opts = ["Todos"] + sorted(df["UF"].unique().tolist())
        uf_sel = fc1.selectbox("UF", uf_opts)
        nome_filter = fc2.text_input("Buscar por nome")

    if uf_sel != "Todos":
        df = df[df["UF"] == uf_sel]
    if nome_filter:
        mask = (
            df["Razão Social"].str.contains(nome_filter, case=False, na=False) |
            df["Nome Fantasia"].str.contains(nome_filter, case=False, na=False)
        )
        df = df[mask]

    st.dataframe(
        df.sort_values("Dist (km)"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Dist (km)": st.column_config.NumberColumn(format="%.2f km"),
            "CNPJ": st.column_config.TextColumn(width="medium"),
            "Razão Social": st.column_config.TextColumn(width="large"),
        },
    )

    # Download buttons
    dc1, dc2 = st.columns(2)
    dc1.download_button(
        "⬇️ Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="empresas.csv",
        mime="text/csv",
        use_container_width=True,
    )
    import json as _json
    dc2.download_button(
        "⬇️ Baixar JSON",
        data=_json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="empresas.json",
        mime="application/json",
        use_container_width=True,
    )

# ── Mapa ──────────────────────────────────────────────────────────────────────
with tab_mapa:
    m = folium.Map(
        location=[result.lat_centro, result.lng_centro],
        zoom_start=13,
        tiles="CartoDB positron",
    )

    # radius circle
    folium.Circle(
        location=[result.lat_centro, result.lng_centro],
        radius=raio * 1000,
        color="#3b82f6",
        fill=True,
        fill_opacity=0.08,
        weight=2,
    ).add_to(m)

    # center marker
    folium.Marker(
        location=[result.lat_centro, result.lng_centro],
        tooltip="Endereço buscado",
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(m)

    # company markers
    for e in result.empresas:
        if e.lat and e.lng:
            cnpj = e.cnpj.zfill(14)
            cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}" \
                       if e.cnpj != "00000000000000" else "N/D"
            popup_html = f"""
                <b>{e.razao_social}</b><br>
                {f'<i>{e.nome_fantasia}</i><br>' if e.nome_fantasia else ''}
                CNPJ: {cnpj_fmt}<br>
                {e.logradouro}, {e.numero} — {e.bairro}<br>
                {e.municipio}/{e.uf} — CEP {e.cep}<br>
                {f'Tel: {e.telefone}' if e.telefone else ''}
            """
            folium.Marker(
                location=[e.lat, e.lng],
                tooltip=e.nome_fantasia or e.razao_social,
                popup=folium.Popup(popup_html, max_width=280),
                icon=folium.Icon(color="red", icon="building", prefix="fa"),
            ).add_to(m)

    st_folium(m, use_container_width=True, height=520)
