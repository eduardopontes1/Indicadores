import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO VISUAL E CSS ---
st.set_page_config(
    page_title="Painel Estrategico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores
CORES = {
    "primaria": "#4682B4",         # SteelBlue (Azul Aço)
    "meta_linha": "#FF6347",       # Tomato
    "texto_escuro": "#2c3e50",
    "texto_claro": "#ffffff",
    "sucesso_bg": "#d4edda",
    "sucesso_text": "#155724",
    "atencao_bg": "#fff3cd",
    "atencao_text": "#856404",
    "neutro_bg": "#e2e3e5",
    "neutro_text": "#383d41",
    "fundo_pag": "#F4F6F8"
}

# CSS PERSONALIZADO (Sombras, Cores e Fontes)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        background-color: {CORES['fundo_pag']};
        color: {CORES['texto_escuro']};
    }}

    /* Títulos com leve sombra para destaque */
    h1 {{ 
        font-size: 2.5rem !important; 
        font-weight: 700 !important; 
        color: {CORES['primaria']};
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }}
    h2 {{ font-size: 1.8rem !important; font-weight: 600 !important; }}
    h3 {{ font-size: 1.4rem !important; font-weight: 600 !important; }}

    /* Customização dos Filtros (Estilo Power BI Suspenso) */
    .stMultiSelect, .stSelectbox {{
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    
    /* Botão Atualizar (Cor SteelBlue) */
    div.stButton > button {{
        background-color: {CORES['primaria']} !important;
        color: white !important;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        width: 100%;
    }}
    div.stButton > button:hover {{
        background-color: #315f85 !important; /* SteelBlue mais escuro no hover */
    }}

    /* Cards de KPI */
    div[data-testid="stMetric"] {{
        background-color: white;
        border-left: 6px solid {CORES['primaria']};
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }}
    div[data-testid="stMetricLabel"] {{ font-size: 1.1rem !important; font-weight: 500; }}
    div[data-testid="stMetricValue"] {{ font-size: 2.2rem !important; font-weight: 700; color: {CORES['primaria']}; }}

    /* Ajuste de margens */
    .block-container {{ padding-top: 2rem; }}
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
        
        # Validação mínima
        if 'Quad' not in df.columns: return pd.DataFrame()

        df = df.dropna(subset=['Gestor', 'Indicador', 'Quad'])
        
        # Conversão para texto
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        if 'Macro' not in df.columns: df['Macro'] = 'Geral'
        df['Macro'] = df['Macro'].astype(str)

        # Conversão numérica segura
        for col in ['Meta', 'Valor']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# Funções Auxiliares
def formatar_valor(valor, nome_indicador):
    nome = str(nome_indicador).lower()
    if any(x in nome for x in ['índice', 'taxa', 'percentual', '%']):
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

# --- 3. BARRA LATERAL (FILTROS POWER BI) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{CORES['primaria']}; text-align:center;'>Filtros</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not df.empty:
        # A. SELETOR DE REFERÊNCIA (Para Texto de Status)
        quads_unicos = sorted(df['Quad'].unique())
        quad_atual_padrao = len(quads_unicos)-1 if quads_unicos else 0
        quad_ref = st.selectbox("Quadrimestre de Referencia (Status):", quads_unicos, index=quad_atual_padrao)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # B. SELETOR DE BARRAS (Para o Gráfico) - O que o usuário pediu
        st.markdown("**Periodos no Grafico (Barras):**")
        quads_barras = st.multiselect(
            "Selecione os períodos visíveis:", # Label hidden via CSS trick or just keep simple
            options=quads_unicos,
            default=quads_unicos, # Por padrão mostra todas
            label_visibility="collapsed"
        )
        if not quads_barras:
            st.warning("Selecione ao menos um período para o gráfico.")
            quads_barras = quads_unicos # Fallback

        st.markdown("---")

        # C. FILTROS HIERÁRQUICOS
        all_macros = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("Macrodesafio:", all_macros, default=all_macros)
        
        gestores_filtrados = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique())
        sel_gestor = st.multiselect("Unidade / Gestor:", gestores_filtrados, default=gestores_filtrados)
        
        st.markdown("---")
        # Botão de Atualizar (Estilizado via CSS acima)
        if st.button("Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

# --- 4. CORPO PRINCIPAL ---
# Aplica filtros de Gestor e Macro
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro))
].copy()

st.title("Painel de Monitoramento Estrategico")

# Abas
tab1, tab2 = st.tabs(["Painel Grafico", "Relatorio Detalhado"])

# === ABA 1: GRÁFICOS ===
with tab1:
    if df_filtered.empty:
        st.info("Utilize os filtros laterais para carregar os dados.")
    else:
        # KPIs do Topo (Baseado na Referência)
        df_kpi = df_filtered[df_filtered['Quad'] == quad_ref].copy()
        if not df_kpi.empty:
            df_kpi['Sucesso'] = df_kpi.apply(check_meta, axis=1)
            total = len(df_kpi)
            batidas = df_kpi['Sucesso'].sum()
            restantes = total - batidas
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Indicadores ({quad_ref})", total)
            c2.metric("Meta Atingida", int(batidas))
            c3.metric("Meta Nao Atingida", int(restantes), delta_color="inverse")
            st.markdown("---")

        # Loop de Gráficos (Lado a Lado)
        df_filtered['Chave'] = df_filtered['Gestor'] + " - " + df_filtered['Indicador']
        lista_indicadores = sorted(df_filtered['Chave'].unique())

        for i in range(0, len(lista_indicadores), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(lista_indicadores):
                    chave = lista_indicadores[i+j]
                    with cols[j]:
                        # Dados Gerais do Indicador
                        dado_full = df_filtered[df_filtered['Chave'] == chave]
                        
                        # Filtra apenas as barras selecionadas pelo usuário
                        dado_plot = dado_full[dado_full['Quad'].isin(quads_barras)].sort_values('Quad')
                        
                        if not dado_plot.empty:
                            meta_val = dado_plot['Meta'].iloc[0]
                            ind_nome = dado_plot['Indicador'].iloc[0]
                            gestor_nome = dado_plot['Gestor'].iloc[0]
                            macro_nome = dado_plot['Macro'].iloc[0]

                            # Cores (Verde SteelBlue ou Tomato Dourado)
                            cores = ["#2E8B57" if check_meta(row) else "#DAA520" for _, row in dado_plot.iterrows()]
                            
                            # Textos formatados
                            textos = [formatar_valor(row['Valor'], ind_nome) for _, row in dado_plot.iterrows()]

                            # Container "Card"
                            with st.container(border=True):
                                fig = go.Figure()

                                # Gráfico de Barras
                                fig.add_trace(go.Bar(
                                    x=dado_plot['Quad'],
                                    y=dado_plot['Valor'],
                                    marker_color=cores,
                                    text=textos,
                                    textposition='auto',
                                    textfont=dict(size=18, color='white', family="Montserrat", weight="bold"),
                                    name="Realizado",
                                    hoverinfo='none' # Remove tooltip interativo
                                ))

                                # Linha da Meta (Tomato Tracejada)
                                fig.add_shape(
                                    type="line",
                                    x0=-0.5, x1=len(dado_plot)-0.5,
                                    y0=meta_val, y1=meta_val,
                                    line=dict(color=CORES['meta_linha'], width=3, dash="dash")
                                )
                                
                                # Texto da Meta
                                meta_txt = formatar_valor(meta_val, ind_nome)
                                fig.add_annotation(
                                    x=len(dado_plot)-0.5, y=meta_val,
                                    text=f" META: {meta_txt} ",
                                    showarrow=False,
                                    yshift=10,
                                    xanchor="right",
                                    font=dict(color=CORES['meta_linha'], size=14, weight="bold")
                                )

                                # Layout Estático
                                fig.update_layout(
                                    title=dict(
                                        text=f"<b>{ind_nome}</b><br><span style='font-size:14px; color:#666;'>{macro_nome} | {gestor_nome}</span>",
                                        font=dict(size=18, color=CORES['primaria'])
                                    ),
                                    height=380,
                                    template="plotly_white",
                                    dragmode=False, # Trava zoom
                                    xaxis=dict(fixedrange=True, type='category', tickfont=dict(size=14, weight="bold")),
                                    yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#eee', tickfont=dict(size=12)),
                                    margin=dict(l=20, r=20, t=60, b=20),
                                    bargap=0.3
                                )
                                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': False, 'displayModeBar': False})

                                # Status Box (Baseado no Quad de Referência)
                                dado_ref_linha = dado_full[dado_full['Quad'] == quad_ref]
                                
                                if not dado_ref_linha.empty:
                                    row_ref = dado_ref_linha.iloc[0]
                                    val_ref_fmt = formatar_valor(row_ref['Valor'], ind_nome)
                                    if check_meta(row_ref):
                                        st.markdown(f"""
                                        <div style="background-color:{CORES['sucesso_bg']}; color:{CORES['sucesso_text']}; 
                                        padding:10px; border-radius:5px; text-align:center; font-weight:bold; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                                        META ATINGIDA EM {quad_ref} (Result: {val_ref_fmt})
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div style="background-color:{CORES['atencao_bg']}; color:{CORES['atencao_text']}; 
                                        padding:10px; border-radius:5px; text-align:center; font-weight:bold; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                                        NAO ATINGIU A META EM {quad_ref} (Result: {val_ref_fmt})
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style="background-color:{CORES['neutro_bg']}; color:{CORES['neutro_text']}; 
                                    padding:10px; border-radius:5px; text-align:center;">
                                    Sem dados lancados para {quad_ref}
                                    </div>
                                    """, unsafe_allow_html=True)

# === ABA 2: RELATÓRIO ===
with tab2:
    st.header(f"Status Detalhado: {quad_ref}")
    st.markdown("---")
    
    lista_ok = []
    lista_nok = []
    lista_sem_dados = []
    
    # Itera sobre TODOS os indicadores filtrados
    for chave in lista_indicadores:
        dado_ind = df_filtered[df_filtered['Chave'] == chave]
        dado_ref = dado_ind[dado_ind['Quad'] == quad_ref]
        
        # Pega dados cadastrais (usa a primeira linha disponível do indicador)
        base = dado_ind.iloc[0]
        macro = base['Macro']
        gestor = base['Gestor']
        ind = base['Indicador']
        
        if dado_ref.empty:
            lista_sem_dados.append(f"**[{macro}] {gestor}** - {ind}")
        else:
            row = dado_ref.iloc[0]
            val_fmt = formatar_valor(row['Valor'], ind)
            meta_fmt = formatar_valor(row['Meta'], ind)
            
            texto = f"**[{macro}] {gestor}** - {ind} <br> *Resultado: {val_fmt} | Meta: {meta_fmt}*"
            
            if check_meta(row): lista_ok.append(texto)
            else: lista_nok.append(texto)
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("Bateram a Meta")
        if lista_ok:
            for i in lista_ok: st.success(i, icon=None) # Sem icone padrao
        else: st.write("-")
        
    with col_b:
        st.subheader("Nao Bateram a Meta")
        if lista_nok:
            for i in lista_nok: st.warning(i, icon=None)
        else: st.write("-")
        
    with col_c:
        st.subheader("Sem Dados no Periodo")
        if lista_sem_dados:
            for i in lista_sem_dados: 
                st.markdown(f"<div style='padding:10px; background-color:white; border-radius:5px; margin-bottom:10px; border-left:4px solid gray;'>{i}</div>", unsafe_allow_html=True)
        else: st.write("Todos os indicadores possuem lancamento.")
