import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO VISUAL E CSS ROBUSTO ---
st.set_page_config(
    page_title="Painel Estratégico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores (SteelBlue e Tomato)
CORES = {
    "primaria": "#4682B4",         # SteelBlue (Azul Aço - solicitado)
    "meta_linha": "#FF6347",       # Tomato (Laranja avermelhado - solicitado)
    "texto": "#1F2937",            # Cinza escuro para leitura
    "sucesso": "#2E8B57",          # SeaGreen
    "falha": "#DAA520",            # GoldenRod
    "fundo_pag": "#F8F9FA"         # Off-white
}

# CSS PERSONALIZADO (Ajuste de Fontes e Filtros)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        color: {CORES['texto']};
        background-color: {CORES['fundo_pag']};
    }}

    /* AUMENTO GERAL DE FONTES (Desktop & Mobile) */
    h1 {{ font-size: 2.8rem !important; font-weight: 800 !important; color: {CORES['primaria']}; }}
    h2 {{ font-size: 2.2rem !important; font-weight: 700 !important; }}
    h3 {{ font-size: 1.6rem !important; font-weight: 600 !important; }}
    p, div, label {{ font-size: 1.2rem !important; }}

    /* ESTILO DOS FILTROS (Tentativa de imitar Power BI) */
    .stMultiSelect, .stSelectbox {{
        background-color: white;
        border-radius: 8px;
    }}
    
    /* Forçar cor SteelBlue nas Tags de seleção */
    span[data-baseweb="tag"] {{
        background-color: {CORES['primaria']} !important;
    }}
    
    /* Aumentar texto dos filtros */
    .stMultiSelect div[data-baseweb="select"] div {{
        font-size: 1.1rem !important; 
    }}

    /* CARDS DE KPI (Sombra e Destaque) */
    div[data-testid="stMetric"] {{
        background-color: white;
        border: 1px solid #e0e0e0;
        border-left: 10px solid {CORES['primaria']};
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
    }}
    div[data-testid="stMetricLabel"] {{ font-size: 1.1rem !important; font-weight: 600; }}
    div[data-testid="stMetricValue"] {{ font-size: 2.5rem !important; font-weight: 700; }}

    /* Remove padding excessivo do topo */
    .block-container {{ padding-top: 1.5rem; }}
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
        
        # Conversões
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        if 'Macro' not in df.columns: df['Macro'] = 'Geral'
        df['Macro'] = df['Macro'].astype(str)

        for col in ['Meta', 'Valor']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = load_data()

# Função auxiliar para formatar porcentagem
def formatar_valor(valor, nome_indicador):
    nome_indicador = nome_indicador.lower()
    # Se tiver palavras chave de %, adiciona o símbolo
    if any(x in nome_indicador for x in ['índice', 'taxa', 'percentual', '%']):
        return f"{valor}%"
    return f"{valor}"

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
    st.markdown(f"<h2 style='color:{CORES['primaria']}; text-align:center;'>Filtros</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not df.empty:
        # Seletor de Foco (Quadrimestre)
        quads = sorted(df['Quad'].unique())
        # Tenta selecionar o último por padrão
        quad_ref = st.selectbox("📅 Quadrimestre de Referência (Foco):", quads, index=len(quads)-1)
        
        st.write("") # Espaço

        # Filtros Multiselect com "Selecionar Todos" implícito
        # Macro
        all_macros = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("📂 Macrodesafio:", all_macros, default=all_macros)
        
        # Gestor
        opcoes_gestor = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique())
        sel_gestor = st.multiselect("bust Unidade / Gestor:", opcoes_gestor, default=opcoes_gestor)
        
        st.markdown("---")
        if st.button("🔄 Atualizar Dados", type="primary"):
            st.cache_data.clear()
            st.rerun()

# --- 4. CORPO DO DASHBOARD ---
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro))
].copy()

st.title("📊 Painel de Metas | TRE-CE")

# Criação das Abas Estilizadas
tab1, tab2 = st.tabs(["📈 VISÃO GRÁFICA DETALHADA", "📋 RELATÓRIO DE LISTAGEM"])

with tab1:
    if df_filtered.empty:
        st.info("⚠️ Utilize os filtros na barra lateral para selecionar os dados.")
    else:
        # KPIs do Quadrimestre
        df_ref = df_filtered[df_filtered['Quad'] == quad_ref].copy()
        
        if not df_ref.empty:
            df_ref['Atingiu'] = df_ref.apply(check_meta, axis=1)
            total = len(df_ref)
            sucesso = df_ref['Atingiu'].sum()
            falha = total - sucesso
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Total de Indicadores", total)
            k2.metric("Atingiram a Meta", int(sucesso))
            k3.metric("Não Atingiram", int(falha), delta_color="inverse")
            st.markdown("---")

        # --- LOOP DE GRÁFICOS ---
        df_filtered['Chave'] = df_filtered['Gestor'] + " - " + df_filtered['Indicador']
        indicadores = sorted(df_filtered['Chave'].unique())

        # Grid de 2 colunas
        for i in range(0, len(indicadores), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(indicadores):
                    chave = indicadores[i+j]
                    with cols[j]:
                        # Dados do gráfico
                        dado_plot = df_filtered[df_filtered['Chave'] == chave].sort_values('Quad')
                        
                        if not dado_plot.empty:
                            meta_val = dado_plot['Meta'].iloc[0]
                            nome_indicador = dado_plot['Indicador'].iloc[0]
                            gestor_atual = dado_plot['Gestor'].iloc[0]
                            
                            # Prepara cores e textos
                            cores = []
                            textos_barras = []
                            
                            for _, row in dado_plot.iterrows():
                                # Cor da barra
                                if check_meta(row): cores.append(CORES['sucesso'])
                                else: cores.append(CORES['falha'])
                                # Texto formatado com % se necessário
                                textos_barras.append(formatar_valor(row['Valor'], nome_indicador))

                            # Container Visual
                            with st.container(border=True):
                                fig = go.Figure()

                                # BARRAS
                                fig.add_trace(go.Bar(
                                    x=dado_plot['Quad'],
                                    y=dado_plot['Valor'],
                                    marker_color=cores,
                                    text=textos_barras,
                                    textposition='auto',
                                    textfont=dict(size=20, color='white', family="Montserrat", weight="bold"), # FONTE GIGANTE DENTRO DA BARRA
                                    name="Realizado",
                                    hoverinfo='none' # Desativa tooltip padrão para evitar poluição no mobile
                                ))

                                # LINHA DA META (Tomato e Tracejada)
                                fig.add_shape(
                                    type="line",
                                    x0=-0.5, x1=len(dado_plot['Quad'])-0.5,
                                    y0=meta_val, y1=meta_val,
                                    line=dict(color=CORES['meta_linha'], width=4, dash="dash") # dash='dash' faz o traço
                                )
                                
                                # RÓTULO DA META (Grudado na linha)
                                texto_meta_fmt = formatar_valor(meta_val, nome_indicador)
                                fig.add_annotation(
                                    x=len(dado_plot['Quad'])-0.5, y=meta_val,
                                    text=f" META: {texto_meta_fmt} ",
                                    showarrow=False,
                                    xanchor="right", yanchor="bottom",
                                    yshift=5,
                                    font=dict(color=CORES['meta_linha'], size=16, weight="bold"),
                                    bgcolor="rgba(255,255,255,0.7)"
                                )

                                # LAYOUT TRAVADO (MOBILE FRIENDLY)
                                fig.update_layout(
                                    title=dict(
                                        text=f"<b>{nome_indicador}</b><br><span style='font-size:16px;color:gray'>{gestor_atual}</span>",
                                        font=dict(size=20)
                                    ),
                                    height=400,
                                    template="plotly_white",
                                    dragmode=False, # TRAVA O ZOOM
                                    xaxis=dict(
                                        type='category', # Barras grossas
                                        fixedrange=True, # Trava eixo X
                                        tickfont=dict(size=16, weight="bold"),
                                        showgrid=False
                                    ),
                                    yaxis=dict(
                                        fixedrange=True, # Trava eixo Y
                                        showgrid=True, 
                                        gridcolor='#e6e6e6',
                                        tickfont=dict(size=14)
                                    ),
                                    margin=dict(l=20, r=20, t=70, b=30),
                                    bargap=0.25
                                )
                                
                                # Renderiza sem a barra de ferramentas (displayModeBar=False)
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})

                                # MENSAGEM DE STATUS (Focada no Quad selecionado)
                                dado_atual = dado_plot[dado_plot['Quad'] == quad_ref]
                                if not dado_atual.empty:
                                    row_atual = dado_atual.iloc[0]
                                    bateu = check_meta(row_atual)
                                    if bateu:
                                        st.markdown(f"<div style='background-color:#d4edda; border: 1px solid #c3e6cb; color:#155724; padding:10px; border-radius:5px; text-align:center; font-weight:bold; font-size: 1.1rem;'>✅ META BATIDA EM {quad_ref}</div>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='background-color:#fff3cd; border: 1px solid #ffeeba; color:#856404; padding:10px; border-radius:5px; text-align:center; font-weight:bold; font-size: 1.1rem;'>⚠️ META NÃO SUPERADA EM {quad_ref}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div style='background-color:#f8f9fa; border: 1px solid #ddd; color:#6c757d; padding:10px; border-radius:5px; text-align:center;'>ℹ️ Aguardando dados de {quad_ref}</div>", unsafe_allow_html=True)

# --- ABA 2: RELATÓRIO (Listas) ---
with tab2:
    st.header(f"Resumo Gerencial: {quad_ref}")
    st.markdown("---")
    
    if not df_filtered.empty:
        lista_sim = []
        lista_nao = []
        
        for chave in indicadores:
            dado = df_filtered[(df_filtered['Chave'] == chave) & (df_filtered['Quad'] == quad_ref)]
            if not dado.empty:
                row = dado.iloc[0]
                val_fmt = formatar_valor(row['Valor'], row['Indicador'])
                meta_fmt = formatar_valor(row['Meta'], row['Indicador'])
                
                texto = f"**{row['Gestor']}** | {row['Indicador']} (Resultado: {val_fmt} / Meta: {meta_fmt})"
                
                if check_meta(row): lista_sim.append(texto)
                else: lista_nao.append(texto)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ Metas Alcançadas")
            if lista_sim:
                for i in lista_sim: st.success(i)
            else: st.info("Nenhum indicador.")
            
        with c2:
            st.subheader("⚠️ Metas Não Alcançadas")
            if lista_nao:
                for i in lista_nao: st.warning(i)
            else: st.success("Todos os indicadores selecionados bateram a meta!")
