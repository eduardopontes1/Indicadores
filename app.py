import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO VISUAL E CSS PREMIUM ---
st.set_page_config(
    page_title="Painel Estrategico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta Corporativa (SteelBlue & Tons Neutros)
CORES = {
    "primaria": "#4682B4",         # SteelBlue Principal
    "secundaria": "#2C3E50",       # Azul Noturno (Texto)
    "destaque_meta": "#FF6347",    # Tomato (Laranja avermelhado)
    "sucesso": "#2E8B57",          # SeaGreen
    "atencao": "#DAA520",          # GoldenRod
    "fundo_pag": "#F4F6F9",        # Cinza Gelo (Fundo Power BI)
    "branco": "#FFFFFF"
}

# CSS PERSONALIZADO (Design System)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        background-color: {CORES['fundo_pag']};
        color: {CORES['secundaria']};
    }}

    /* Títulos com Sombra Leve */
    h1 {{ 
        font-size: 2.5rem !important; 
        font-weight: 700 !important; 
        color: {CORES['primaria']};
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }}
    h2, h3 {{ 
        color: {CORES['secundaria']}; 
        font-weight: 600;
    }}

    /* ESTILO DOS FILTROS (Imitando Dropdown Power BI) */
    .stMultiSelect label, .stSelectbox label {{
        color: {CORES['primaria']} !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }}
    
    .stMultiSelect div[data-baseweb="select"] {{
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #d1d5db;
    }}

    /* Botão Atualizar (Mesma cor dos filtros) */
    div.stButton > button {{
        background-color: {CORES['primaria']};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: #315f85; /* SteelBlue mais escuro */
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        color: white;
    }}

    /* CARDS DE KPI */
    div[data-testid="stMetric"] {{
        background-color: white;
        border-left: 6px solid {CORES['primaria']};
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }}
    
    /* Container dos Gráficos */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}

    /* Ajuste de Espaçamento Topo */
    .block-container {{ padding-top: 2rem; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DADOS ---
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
        
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        if 'Macro' not in df.columns: df['Macro'] = 'Geral'
        df['Macro'] = df['Macro'].astype(str)

        for col in ['Meta', 'Valor']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro de conexao: {e}")
        return pd.DataFrame()

df = load_data()

def formatar_valor(valor, nome_indicador):
    nome_indicador = nome_indicador.lower()
    if any(x in nome_indicador for x in ['indice', 'taxa', 'percentual', '%']):
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

# --- 3. BARRA LATERAL (FILTROS POWER BI STYLE) ---
with st.sidebar:
    st.title("Filtros")
    st.markdown("Use as opcoes abaixo para segmentar a visao.")
    st.markdown("---")
    
    if not df.empty:
        # SELETOR DE PERÍODOS DO GRÁFICO (Eixo X)
        # Por padrão, seleciona TODOS
        todos_periodos = sorted(df['Quad'].unique())
        sel_eixo_x = st.multiselect(
            "Periodos no Grafico (Barras):", 
            todos_periodos, 
            default=todos_periodos,
            help="Escolha quais barras aparecem no grafico."
        )
        
        st.write("") # Espaço

        # QUADRIMESTRE DE REFERÊNCIA (Para cálculo de meta)
        # Pega o último selecionado no filtro acima ou o último da lista total
        opcoes_ref = sel_eixo_x if sel_eixo_x else todos_periodos
        idx_padrao = len(opcoes_ref)-1 if options_ref else 0
        quad_ref = st.selectbox(
            "Periodo de Analise (Status Meta):", 
            opcoes_ref, 
            index=idx_padrao
        )
        
        st.markdown("---")

        # FILTROS HIERÁRQUICOS
        all_macros = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("Macrodesafio:", all_macros, default=all_macros)
        
        opcoes_gestor = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique())
        sel_gestor = st.multiselect("Unidade / Gestor:", opcoes_gestor, default=opcoes_gestor)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ATUALIZAR DADOS"):
            st.cache_data.clear()
            st.rerun()

# --- 4. CORPO DO DASHBOARD ---
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro))
].copy()

st.title("Painel de Monitoramento Estrategico")

# Abas Limpas
tab1, tab2 = st.tabs(["DASHBOARD GRAFICO", "RELATORIO DETALHADO"])

with tab1:
    if df_filtered.empty or not sel_eixo_x:
        st.info("Selecione os filtros na barra lateral para visualizar os dados.")
    else:
        # KPIs do Período de Referência
        df_kpi = df_filtered[df_filtered['Quad'] == quad_ref].copy()
        
        total = 0
        sucesso = 0
        falha = 0
        
        if not df_kpi.empty:
            df_kpi['Atingiu'] = df_kpi.apply(check_meta, axis=1)
            total = len(df_kpi)
            sucesso = df_kpi['Atingiu'].sum()
            falha = total - sucesso
            
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Indicadores em {quad_ref}", total)
        k2.metric("Meta Atingida", int(sucesso))
        k3.metric("Nao Atingida", int(falha), delta_color="inverse")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- LOOP DE GRÁFICOS ---
        df_filtered['Chave'] = df_filtered['Gestor'] + " - " + df_filtered['Indicador']
        indicadores = sorted(df_filtered['Chave'].unique())

        for i in range(0, len(indicadores), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(indicadores):
                    chave = indicadores[i+j]
                    with cols[j]:
                        # Filtra apenas os períodos selecionados no Eixo X
                        dado_plot = df_filtered[
                            (df_filtered['Chave'] == chave) & 
                            (df_filtered['Quad'].isin(sel_eixo_x))
                        ].sort_values('Quad')
                        
                        if not dado_plot.empty:
                            meta_val = dado_plot['Meta'].iloc[0]
                            nome_ind = dado_plot['Indicador'].iloc[0]
                            gestor_nm = dado_plot['Gestor'].iloc[0]
                            
                            # Cores e Textos
                            cores = [CORES['sucesso'] if check_meta(r) else CORES['atencao'] for _, r in dado_plot.iterrows()]
                            textos = [formatar_valor(r['Valor'], nome_ind) for _, r in dado_plot.iterrows()]

                            # GRÁFICO
                            with st.container(): # Card branco automático pelo CSS
                                fig = go.Figure()

                                fig.add_trace(go.Bar(
                                    x=dado_plot['Quad'], y=dado_plot['Valor'],
                                    marker_color=cores, text=textos,
                                    textposition='auto',
                                    textfont=dict(size=18, color='white', family="Montserrat", weight="bold"),
                                    hoverinfo='none'
                                ))

                                # Linha Meta
                                fig.add_shape(
                                    type="line", x0=-0.5, x1=len(dado_plot)-0.5,
                                    y0=meta_val, y1=meta_val,
                                    line=dict(color=CORES['destaque_meta'], width=3, dash="dash")
                                )
                                
                                txt_meta = formatar_valor(meta_val, nome_ind)
                                fig.add_annotation(
                                    x=len(dado_plot)-0.5, y=meta_val,
                                    text=f" META: {txt_meta} ",
                                    showarrow=False, xanchor="right", yshift=10,
                                    font=dict(color=CORES['destaque_meta'], size=14, weight="bold"),
                                    bgcolor="rgba(255,255,255,0.9)"
                                )

                                fig.update_layout(
                                    title=dict(
                                        text=f"<b>{nome_ind}</b><br><span style='font-size:16px;color:#555'>{gestor_nm}</span>",
                                        font=dict(size=18, color=CORES['primaria'])
                                    ),
                                    height=380, template="plotly_white",
                                    dragmode=False, # Sem Zoom
                                    xaxis=dict(fixedrange=True, type='category', tickfont=dict(size=14, weight="bold"), showgrid=False),
                                    yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#eee', tickfont=dict(size=12)),
                                    margin=dict(l=20, r=20, t=60, b=20),
                                    bargap=0.3
                                )
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                                # Status Box
                                dado_ref_linha = dado_plot[dado_plot['Quad'] == quad_ref]
                                if not dado_ref_linha.empty:
                                    row_r = dado_ref_linha.iloc[0]
                                    if check_meta(row_r):
                                        st.success(f"✅ {quad_ref}: Meta Atingida")
                                    else:
                                        st.warning(f"⚠️ {quad_ref}: Nao Atingida")
                                else:
                                    st.info(f"ℹ️ Sem dados em {quad_ref}")

# --- ABA 2: RELATÓRIO ---
with tab2:
    st.markdown(f"### Status Geral - Referencia: {quad_ref}")
    st.markdown("---")
    
    lst_sim = []
    lst_nao = []
    lst_sem = []
    
    # Processamento para Relatório
    todos_indicadores_filtrados = df_filtered['Chave'].unique()
    
    for chave in todos_indicadores_filtrados:
        # Pega a linha específica do quadrimestre de referência
        linha = df_filtered[(df_filtered['Chave'] == chave) & (df_filtered['Quad'] == quad_ref)]
        
        # Pega info geral do indicador (mesmo se não tiver dado no quad atual, para saber quem é)
        info_ind = df_filtered[df_filtered['Chave'] == chave].iloc[0]
        macro_nm = info_ind['Macro']
        gestor_nm = info_ind['Gestor']
        ind_nm = info_ind['Indicador']
        
        texto_base = f"**{macro_nm}** > **{gestor_nm}** | {ind_nm}"
        
        if not linha.empty:
            row = linha.iloc[0]
            val_f = formatar_valor(row['Valor'], ind_nm)
            meta_f = formatar_valor(row['Meta'], ind_nm)
            detalhe = f"{texto_base} <br><span style='font-size:0.9rem; color:gray'>Resultado: {val_f} | Meta: {meta_f}</span>"
            
            if check_meta(row): lst_sim.append(detalhe)
            else: lst_nao.append(detalhe)
        else:
            lst_sem.append(texto_base)

    # Exibição em Colunas
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"<div style='background-color:#d4edda; padding:10px; border-radius:5px; color:#155724; font-weight:bold; text-align:center'>✅ METAS ATINGIDAS ({len(lst_sim)})</div>", unsafe_allow_html=True)
        st.write("")
        for i in lst_sim: 
            st.markdown(f"<div style='background:white; padding:10px; margin-bottom:5px; border-radius:5px; box-shadow:0 1px 2px rgba(0,0,0,0.1)'>{i}</div>", unsafe_allow_html=True)
            
    with c2:
        st.markdown(f"<div style='background-color:#fff3cd; padding:10px; border-radius:5px; color:#856404; font-weight:bold; text-align:center'>⚠️ NAO ATINGIDAS ({len(lst_nao)})</div>", unsafe_allow_html=True)
        st.write("")
        for i in lst_nao: 
            st.markdown(f"<div style='background:white; padding:10px; margin-bottom:5px; border-radius:5px; box-shadow:0 1px 2px rgba(0,0,0,0.1)'>{i}</div>", unsafe_allow_html=True)

    with c3:
        st.markdown(f"<div style='background-color:#e2e3e5; padding:10px; border-radius:5px; color:#383d41; font-weight:bold; text-align:center'>ℹ️ SEM DADOS NO PERIODO ({len(lst_sem)})</div>", unsafe_allow_html=True)
        st.write("")
        for i in lst_sem: 
            st.markdown(f"<div style='background:white; padding:10px; margin-bottom:5px; border-radius:5px; box-shadow:0 1px 2px rgba(0,0,0,0.1)'>{i}</div>", unsafe_allow_html=True)
