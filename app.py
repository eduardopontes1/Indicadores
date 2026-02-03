import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Monitoramento Estratégico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta SteelBlue (Azul Aço e Tons Profissionais)
CORES = {
    "primaria": "#4682B4",         # SteelBlue
    "secundaria": "#2c3e50",       # Azul Escuro (Texto)
    "sucesso": "#2E8B57",          # SeaGreen (Verde mais sóbrio)
    "atencao": "#DAA520",          # GoldenRod (Substitui o vermelho/laranja)
    "meta_linha": "#1e3799",       # Azul Royal Escuro para a linha da meta
    "fundo": "#F0F2F6"             # Cinza muito suave
}

# CSS para aumentar fontes (Desktop Friendly)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        background-color: {CORES['fundo']};
        color: {CORES['secundaria']};
    }}

    /* Aumentando Títulos */
    h1 {{ font-size: 2.5rem !important; font-weight: 800 !important; color: {CORES['primaria']}; }}
    h2 {{ font-size: 2.0rem !important; font-weight: 700 !important; }}
    h3 {{ font-size: 1.5rem !important; font-weight: 600 !important; }}
    
    /* Aumentando textos dos filtros e widgets */
    .stMultiSelect, .stSelectbox {{ font-size: 1.2rem !important; }}
    label {{ font-size: 1.3rem !important; font-weight: 600 !important; color: {CORES['primaria']} !important; }}
    
    /* Estilo dos Cards de KPI */
    div[data-testid="stMetric"] {{
        background-color: #ffffff;
        border-left: 8px solid {CORES['primaria']};
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-radius: 5px;
    }}
    /* Aumenta o número dentro do card */
    div[data-testid="stMetricValue"] {{ font-size: 2.2rem !important; }}
    
    /* Status Box abaixo do gráfico */
    .status-box {{
        padding: 15px;
        border-radius: 5px;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
        margin-top: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1Fvo48kFkoTdR9vacDjdasrh6s2MBxcGGFiS53EZcjb8"
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    try:
        df = pd.read_csv(url_csv)
        df.columns = df.columns.str.strip()
        cols_map = {'Semestre': 'Quad', 'Periodo': 'Quad', 'Período': 'Quad'}
        df = df.rename(columns=lambda x: cols_map.get(x, x))
        df = df.dropna(subset=['Gestor', 'Indicador', 'Quad'])
        
        # Converte tudo para string ou numero
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        if 'Macro' not in df.columns: df['Macro'] = 'Geral'
        df['Macro'] = df['Macro'].astype(str)

        for col in ['Meta', 'Valor']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

df = load_data()

def check_meta(row):
    try:
        meta, valor = float(row['Meta']), float(row['Valor'])
        sentido = str(row.get('Sentido', '')).lower()
        if 'superar' in sentido or '>=' in sentido: return valor >= meta
        elif 'manter' in sentido or '<=' in sentido: return valor <= meta
        return valor >= meta 
    except: return False

# --- 3. BARRA LATERAL (FILTROS) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{CORES['primaria']}'>Filtros</h2>", unsafe_allow_html=True)
    
    if not df.empty:
        # Seletor de Referência (Foco)
        quads = sorted(df['Quad'].unique())
        quad_ref = st.selectbox("Quadrimestre de Referência (Foco):", quads, index=len(quads)-1)
        st.markdown("---")

        # Filtros Multiselect "Suspensos"
        # 1. Macrodesafio
        all_macros = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("Selecione Macrodesafio:", all_macros, default=all_macros)
        
        # 2. Gestor (Filtrado pelo Macro)
        filtered_gestor_options = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique())
        sel_gestor = st.multiselect("Selecione Unidade/Gestor:", filtered_gestor_options, default=filtered_gestor_options)
        
        # Botão Limpar Cache
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Base", type="secondary"):
            st.cache_data.clear()
            st.rerun()

# --- 4. CORPO DO DASHBOARD ---
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro))
].copy()

st.title("Painel de Metas | TRE-CE")

# Criação das Abas
tab1, tab2 = st.tabs(["VISÃO GRÁFICA DETALHADA", "RELATÓRIO DE LISTAGEM"])

with tab1:
    if df_filtered.empty:
        st.warning("⚠️ Selecione ao menos um Gestor ou Macrodesafio nos filtros laterais.")
    else:
        # KPIs do Quadrimestre de Referência
        df_ref = df_filtered[df_filtered['Quad'] == quad_ref].copy()
        if not df_ref.empty:
            df_ref['Atingiu'] = df_ref.apply(check_meta, axis=1)
            
            total = len(df_ref)
            sucesso = df_ref['Atingiu'].sum()
            falha = total - sucesso
            
            k1, k2, k3 = st.columns(3)
            k1.metric(f"Total de Indicadores ({quad_ref})", total)
            k2.metric("Atingiram a Meta", int(sucesso))
            k3.metric("Não Atingiram", int(falha), delta_color="inverse")
            st.markdown("---")

        # --- LOOP DE GRÁFICOS ---
        df_filtered['Chave'] = df_filtered['Gestor'] + " - " + df_filtered['Indicador']
        indicadores = sorted(df_filtered['Chave'].unique())

        # Layout em 2 colunas
        for i in range(0, len(indicadores), 2):
            cols = st.columns(2)
            
            for j in range(2):
                if i + j < len(indicadores):
                    chave = indicadores[i+j]
                    with cols[j]:
                        # Preparação dos dados
                        dado_plot = df_filtered[df_filtered['Chave'] == chave].sort_values('Quad')
                        meta_val = dado_plot['Meta'].iloc[0]
                        
                        # Cores das barras
                        cores = [CORES['sucesso'] if check_meta(row) else CORES['atencao'] for _, row in dado_plot.iterrows()]

                        # Container com borda (Card Visual)
                        with st.container(border=True):
                            fig = go.Figure()

                            # Barras
                            fig.add_trace(go.Bar(
                                x=dado_plot['Quad'],
                                y=dado_plot['Valor'],
                                marker_color=cores,
                                text=dado_plot['Valor'],
                                textposition='auto', # Texto dentro da barra
                                textfont=dict(size=16, color='white', family="Montserrat", weight="bold"),
                                name="Realizado"
                            ))

                            # LINHA DA META (Corrigida e Visível)
                            fig.add_shape(
                                type="line",
                                x0=-0.5, x1=len(dado_plot['Quad'])-0.5, # Cobre todo o eixo X
                                y0=meta_val, y1=meta_val,
                                line=dict(color=CORES['meta_linha'], width=4, dash="solid")
                            )
                            
                            # Rótulo da Meta
                            fig.add_annotation(
                                x=len(dado_plot['Quad'])-0.5, y=meta_val,
                                text=f" META: {meta_val} ",
                                showarrow=False,
                                xanchor="right", yanchor="bottom",
                                font=dict(color=CORES['meta_linha'], size=14, weight="bold"),
                                bgcolor="rgba(255,255,255,0.8)"
                            )

                            # Layout Otimizado para "Barras Grossas"
                            fig.update_layout(
                                title=dict(text=f"<b>{chave}</b>", font=dict(size=18)),
                                height=380,
                                template="plotly_white",
                                xaxis=dict(
                                    type='category', # ISSO ENGROSSA AS BARRAS
                                    tickfont=dict(size=14, weight="bold"),
                                    showgrid=False
                                ),
                                yaxis=dict(
                                    showgrid=True, 
                                    gridcolor='#e6e6e6',
                                    tickfont=dict(size=14)
                                ),
                                margin=dict(l=20, r=20, t=50, b=20),
                                bargap=0.3 # Ajuste a grossura (0.1 = muito grosso, 0.5 = fino)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)

                            # Mensagem de Status (Foco no Quadrimestre de Referência)
                            dado_atual = dado_plot[dado_plot['Quad'] == quad_ref]
                            if not dado_atual.empty:
                                val_atual = dado_atual['Valor'].iloc[0]
                                bateu = check_meta(dado_atual.iloc[0])
                                if bateu:
                                    st.markdown(f"<div style='background-color:#d4edda; color:#155724; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>✅ META BATIDA EM {quad_ref}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div style='background-color:#fff3cd; color:#856404; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>⚠️ META NÃO ATINGIDA EM {quad_ref}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='background-color:#e2e3e5; color:#383d41; padding:10px; border-radius:5px; text-align:center;'>ℹ️ Sem dados para {quad_ref}</div>", unsafe_allow_html=True)

# --- ABA 2: RELATÓRIO (Listas) ---
with tab2:
    st.header(f"Resumo Gerencial: {quad_ref}")
    st.markdown("---")
    
    if not df_filtered.empty:
        # Prepara listas
        lista_sim = []
        lista_nao = []
        
        # Itera sobre os dados filtrados
        for chave in indicadores:
            dado = df_filtered[(df_filtered['Chave'] == chave) & (df_filtered['Quad'] == quad_ref)]
            if not dado.empty:
                row = dado.iloc[0]
                texto = f"**{row['Gestor']}** - {row['Indicador']} (Realizado: {row['Valor']} | Meta: {row['Meta']})"
                if check_meta(row):
                    lista_sim.append(texto)
                else:
                    lista_nao.append(texto)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ Metas Alcançadas")
            for i in lista_sim: st.success(i)
            if not lista_sim: st.info("Nenhum indicador neste grupo.")
            
        with c2:
            st.subheader("⚠️ Metas Não Alcançadas")
            for i in lista_nao: st.warning(i)
            if not lista_nao: st.success("Todos os indicadores bateram a meta!")
