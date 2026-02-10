import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import numpy as np

# ==============================================================================
# 1. CONFIGURAÇÃO E AUTENTICAÇÃO SIMPLIFICADA
# ==============================================================================
st.set_page_config(
    page_title="Acesso Restrito | TRE-CE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE LOGIN ---
USUARIOS = {
    "TRE-CE": "TReCe.2026"
}

def verificar_login():
    # Inicializa variáveis de sessão
    if "logado" not in st.session_state:
        st.session_state["logado"] = False
    
    # Se não estiver logado, exibe a tela de login
    if not st.session_state["logado"]:
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style='background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #666;'>
                    <h1 style='color: #666; font-size: 2rem;'>🔒 Acesso Restrito</h1>
                    <p style='color: #666;'>Painel de Monitoramento Estratégico TRE-CE</p>
                </div>
                <br>
                """, 
                unsafe_allow_html=True
            )
            
            # --- LOGIN DIRETO (SEM 2FA) ---
            usuario = st.text_input("Usuário", placeholder="Digite seu usuário...")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha...")
            
            if st.button("ACESSAR SISTEMA", type="primary"):
                if usuario in USUARIOS and USUARIOS[usuario] == senha:
                    st.session_state["logado"] = True
                    st.success("Login realizado com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        # Bloqueia o restante do app enquanto não logar
        st.stop()

verificar_login()

# ==============================================================================
# 2. DESIGN E DADOS (MANTIDO)
# ==============================================================================

CORES = {
    "primaria": "#4682B4",         # SteelBlue
    "primaria_dark": "#315f85",    
    "meta_linha": "#FF6347",       # Tomato
    "texto": "#2C3E50",            
    "fundo": "#F4F6F9",            
    "sucesso": "#2E8B57",          # Verde
    "atencao": "#DAA520",          # Dourado
    "sucesso_bg": "#D4EDDA", "sucesso_txt": "#155724",      
    "falha_bg": "#FFF3CD",   "falha_txt": "#856404",        
    "neutro_bg": "#E2E3E5",  "neutro_txt": "#383D41"        
}

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        background-color: {CORES['fundo']};
        color: {CORES['texto']};
    }}
    
    h1 {{ font-size: 3rem !important; font-weight: 800 !important; color: {CORES['primaria']}; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }}
    h2 {{ font-size: 2.2rem !important; font-weight: 700 !important; color: {CORES['texto']}; }}
    div.stButton > button {{
        background-color: {CORES['primaria']}; color: white; font-size: 1.2rem !important;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s;
    }}
    div.stButton > button:hover {{ background-color: {CORES['primaria_dark']}; color: white; }}
    div[data-testid="stMetric"] {{
        background-color: white; border-left: 10px solid {CORES['primaria']};
        padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }}
    div[data-testid="stMetricValue"] {{ font-size: 2.5rem !important; font-weight: 800; }}
    .block-container {{ padding-top: 1.5rem; }}
    </style>
    """, unsafe_allow_html=True)

# Lógica de Polaridade
def definir_polaridade_inteligente(nome_indicador, valor_planilha):
    nome = str(nome_indicador).lower()
    palavras_chave_negativas = ['tempo', 'taxa de congestionamento', 'custo', 'despesa', 'absenteísmo', 'pendência', 'acervo']
    if any(p in nome for p in palavras_chave_negativas): return -1
    try:
        val = float(valor_planilha)
        if val == 1 or val == -1: return val
    except: pass
    return 1

@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1oefuUAE4Vlt9WLecgS0_4ZZZvAfV_c-t5M6nT3YOMjs"
    url_csv = f"https://docs.google.com/spreadsheets/d/1Ue4EuT4-NOJwF4VesxFvktkM9kEJdVe7E5i7n8PkBds/edit?usp=sharing"
    if "/edit" in url_csv: url_csv = url_csv.replace("/edit?usp=sharing", "/export?format=csv")

    try:
        df = pd.read_csv(url_csv)
        df.columns = df.columns.str.strip()
        
        # Normalização de Colunas
        if 'Unidade' in df.columns: df['Gestor'] = df['Unidade']
        else: df['Gestor'] = df['Gestor'].astype(str)

        if 'Resultado_Num' in df.columns: df['Valor'] = df['Resultado_Num']
        elif 'Resultado' in df.columns:
             df['Valor'] = pd.to_numeric(df['Resultado'].astype(str).str.replace(',', '.'), errors='coerce')

        if 'Meta_Num' in df.columns: df['Meta'] = df['Meta_Num']
        elif 'Meta' in df.columns:
             df['Meta'] = pd.to_numeric(df['Meta'].astype(str).str.replace(',', '.'), errors='coerce')
            
        if 'Macrodesafio' in df.columns: df['Macro'] = df['Macrodesafio']
        elif 'Macro' not in df.columns: df['Macro'] = 'Geral'

        df['Ano'] = df['Ano'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Quadrimestre'] = df['Quadrimestre'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Quad'] = df['Ano'] + "." + df['Quadrimestre']
        
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Macro'] = df['Macro'].astype(str)

        for col in ['Meta', 'Valor']:
            if col not in df.columns: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        polaridades_corrigidas = []
        for index, row in df.iterrows():
            pol_original = row.get('Polaridade', 1)
            pol_nova = definir_polaridade_inteligente(row['Indicador'], pol_original)
            polaridades_corrigidas.append(pol_nova)
            
        df['Polaridade'] = polaridades_corrigidas
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = load_data()

def formatar_valor(valor, nome_indicador):
    nome_indicador = nome_indicador.lower()
    if any(x in nome_indicador for x in ['indice', 'taxa', 'percentual', '%']):
        return f"{valor:.2f}%"
    return f"{valor:.2f}"

def check_meta(row):
    try:
        meta = float(row['Meta'])
        valor = float(row['Valor'])
        polaridade = row['Polaridade']
        
        if polaridade == 1:    
            return valor >= meta
        elif polaridade == -1:
            return valor <= meta
        else:
            return valor >= meta 
    except:
        return False

# ==============================================================================
# 4. BARRA LATERAL (FILTROS)
# ==============================================================================
with st.sidebar:
    st.markdown(f"<h1 style='color:{CORES['primaria']}; font-size:2rem !important; text-align:center'>Filtros</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not df.empty:
        todos_periodos = sorted(df['Quad'].unique())
        sel_eixo_x = st.multiselect("Periodos no Grafico:", todos_periodos, default=todos_periodos)
        st.write("")

        opcoes_ref = sel_eixo_x if sel_eixo_x else todos_periodos
        idx_padrao = len(opcoes_ref)-1 if opcoes_ref else 0
        quad_ref = st.selectbox("Periodo de Referencia:", opcoes_ref, index=idx_padrao)
        st.markdown("---")

        all_macros = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("Macrodesafio:", all_macros, default=all_macros)
        
        if sel_macro:
            gestores_disp = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique())
        else:
            gestores_disp = []  
        sel_gestor = st.multiselect("Unidade / Gestor:", gestores_disp, default=gestores_disp)

        if sel_gestor:
            filtros_ativos = (df['Macro'].isin(sel_macro)) & (df['Gestor'].isin(sel_gestor))
            ind_disp = sorted(df[filtros_ativos]['Indicador'].unique())
        else:
            ind_disp = []
        sel_indicador = st.multiselect("Indicadores Específicos:", ind_disp, default=ind_disp)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ATUALIZAR DADOS"):
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("---")
    if st.button("🚪 SAIR DO SISTEMA"):
        st.session_state["logado"] = False
        st.rerun()

# ==============================================================================
# 5. CORPO DO DASHBOARD (LÓGICA GRÁFICA)
# ==============================================================================
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro)) &
    (df['Indicador'].isin(sel_indicador))
].copy()

if not df_filtered.empty:
    df_filtered['Chave'] = df_filtered['Gestor'] + " - " + df_filtered['Indicador']

st.title("Painel de Monitoramento Estrategico")

tab1, tab2 = st.tabs(["VISAO GRAFICA", "RELATORIO DETALHADO"])

with tab1:
    if df_filtered.empty or not sel_eixo_x:
        st.info("Selecione os filtros para visualizar.")
    else:
        df_kpi = df_filtered[df_filtered['Quad'] == quad_ref].copy()
        total, sucesso, falha = 0, 0, 0
        
        if not df_kpi.empty:
            df_kpi['Atingiu'] = df_kpi.apply(check_meta, axis=1)
            total = len(df_kpi)
            sucesso = df_kpi['Atingiu'].sum()
            falha = total - sucesso
            
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Total em {quad_ref}", total)
        k2.metric("Meta Atingida", int(sucesso))
        k3.metric("Nao Atingida", int(falha), delta_color="inverse")
        
        st.markdown("---")

        indicadores = sorted(df_filtered['Chave'].unique())
        for i in range(0, len(indicadores), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(indicadores):
                    chave = indicadores[i+j]
                    with cols[j]:
                        dado_plot = df_filtered[
                            (df_filtered['Chave'] == chave) & 
                            (df_filtered['Quad'].isin(sel_eixo_x))
                        ].sort_values('Quad')
                        
                        if not dado_plot.empty:
                            nome_ind = dado_plot['Indicador'].iloc[0]
                            macro_nm = dado_plot['Macro'].iloc[0]
                            polaridade_atual = dado_plot['Polaridade'].iloc[0]
                            
                            meta_ref_row = dado_plot[dado_plot['Quad'] == quad_ref]
                            if not meta_ref_row.empty:
                                meta_val = meta_ref_row['Meta'].iloc[0]
                            else:
                                meta_val = dado_plot['Meta'].iloc[-1]
                            
                            # Cores baseadas na meta
                            cores = [CORES['sucesso'] if check_meta(r) else CORES['atencao'] for _, r in dado_plot.iterrows()]
                            textos = [formatar_valor(r['Valor'], nome_ind) for _, r in dado_plot.iterrows()]

                            with st.container():
                                st.markdown(f"<div style='background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:10px;'>", unsafe_allow_html=True)
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=dado_plot['Quad'], y=dado_plot['Valor'],
                                    marker_color=cores, text=textos,
                                    textposition='auto',
                                    textfont=dict(size=18, color='white', family="Montserrat", weight="bold"),
                                    hoverinfo='none'
                                ))
                                
                                fig.add_shape(type="line", x0=-0.5, x1=len(dado_plot)-0.5,
                                    y0=meta_val, y1=meta_val,
                                    line=dict(color=CORES['meta_linha'], width=3, dash="dash")
                                )
                                
                                seta = "⬆️ (Maior é Melhor)" if polaridade_atual == 1 else "⬇️ (Menor é Melhor)"
                                txt_meta = formatar_valor(meta_val, nome_ind)
                                
                                fig.add_annotation(
                                    x=len(dado_plot)-0.5, y=meta_val,
                                    text=f" META: {txt_meta} ",
                                    showarrow=False, xanchor="right", yshift=10,
                                    font=dict(color=CORES['meta_linha'], size=14, weight="bold"),
                                    bgcolor="rgba(255,255,255,0.9)"
                                )
                                fig.update_layout(
                                    title=dict(text=f"<b>{nome_ind}</b><br><span style='font-size:14px;color:#555'>{macro_nm} | {seta}</span>", font=dict(size=18, color=CORES['primaria'])),
                                    height=380, template="plotly_white", dragmode=False,
                                    xaxis=dict(fixedrange=True, type='category', tickfont=dict(size=14, weight="bold"), showgrid=False),
                                    yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#eee', tickfont=dict(size=12)),
                                    margin=dict(l=20, r=20, t=80, b=20), bargap=0.3
                                )
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
                                st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown(f"<h3 style='color:{CORES['primaria']}'>Relatorio Sintetico - Referencia: {quad_ref}</h3>", unsafe_allow_html=True)
    # ... (MANTIDA A LOGICA DE EXIBIÇÃO DO TAB2 QUE É APENAS VISUALIZAÇÃO DE TEXTO) ...
    # A lógica é idêntica à do código original, apenas exibindo os cards.
