import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import numpy as np

# ==============================================================================
# 1. CONFIGURAÇÃO E AUTENTICAÇÃO
# ==============================================================================
st.set_page_config(
    page_title="Painel Estratégico | TRE-CE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE LOGIN ---
# Usuários e Senhas definidos
USUARIOS = {
    "TRE-CE": "TReCe.2026",
    "admin": "aDMiN.2026",
    "eduardo": "123" # Para testes rápidos
}

def verificar_login():
    """Bloqueia o app até o login ser feito"""
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if not st.session_state["logado"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style='background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #666;'>
                    <h1 style='color: #666; font-size: 2rem;'>🔒 Acesso Restrito</h1>
                    <p style='color: #666;'>Monitoramento Estratégico TRE-CE</p>
                </div>
                <br>
                """, 
                unsafe_allow_html=True
            )
            
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
        st.stop()

# Executa o login antes de carregar o resto
verificar_login()

# ==============================================================================
# 2. DESIGN E ESTILO (CSS)
# ==============================================================================
CORES = {
    "primaria": "#4682B4",         # Azul Steel
    "meta_linha": "#FF6347",       # Tomate (Linha da meta)
    "texto": "#2C3E50",            # Cinza Escuro
    "fundo": "#F4F6F9",            # Cinza Claro Fundo
    "sucesso": "#2E8B57",          # Verde
    "atencao": "#C0392B",          # Vermelho
    "sucesso_bg": "#D4EDDA", "sucesso_txt": "#155724",
    "falha_bg": "#F8D7DA",   "falha_txt": "#721C24"
}

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        background-color: {CORES['fundo']};
        color: {CORES['texto']};
    }}
    
    /* Títulos */
    h1 {{ color: {CORES['primaria']}; font-weight: 800 !important; }}
    h2, h3 {{ color: {CORES['texto']}; font-weight: 700 !important; }}
    
    /* Cards de Métricas */
    div[data-testid="stMetric"] {{
        background-color: white;
        border-left: 8px solid {CORES['primaria']};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    
    /* Botões */
    div.stButton > button {{
        width: 100%;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. MOTOR DE DADOS (Carregamento e Lógica)
# ==============================================================================

@st.cache_data(ttl=60)
def load_data():
    """Carrega os dados já tratados pelo R"""
    
    # CAMINHO DO ARQUIVO (Aponte para o CSV exportado do R)
    arquivo = "dados_dashboard.csv" 
    # Se for usar Google Sheets, substitua pela URL do CSV exportado
    
    try:
        df = pd.read_csv(arquivo)
        
        # 1. Limpeza de Nomes de Coluna
        df.columns = df.columns.str.strip()
        
        # 2. Filtragem de Segurança (Remove linhas sem números válidos)
        # Como o R já criou Resultado_Num e Meta_Num, usamos eles direto.
        df = df.dropna(subset=['Meta_Num', 'Resultado_Num'])
        
        # 3. Tratamento de Polaridade (Garante que não tenha vazios)
        if 'Polaridade' in df.columns:
            df['Polaridade'] = pd.to_numeric(df['Polaridade'], errors='coerce').fillna(1)
        else:
            df['Polaridade'] = 1 # Padrão Maior Melhor

        # 4. Criar Coluna de Período para o Gráfico (Eixo X ordenado)
        # Ex: "2021.1", "2021.2"
        df['Ano'] = df['Ano'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Quadrimestre'] = df['Quadrimestre'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Periodo_Grafico'] = df['Ano'] + "." + df['Quadrimestre']
        
        # 5. Criar Chave Única (Para iterar nos gráficos)
        df['Chave'] = df['Unidade'] + " - " + df['Indicador']
        
        return df

    except Exception as e:
        st.error(f"Erro ao carregar '{arquivo}'. Verifique se o arquivo está na pasta. Detalhe: {e}")
        return pd.DataFrame()

df = load_data()

def formatar_valor(valor):
    """Formata números para exibição (BR)"""
    try:
        if pd.isna(valor): return "-"
        if valor >= 1000:
            return f"{valor:,.0f}".replace(',', '.')
        elif isinstance(valor, float):
            return f"{valor:.2f}".replace('.', ',')
        return str(valor)
    except:
        return str(valor)

def check_meta(row):
    """Verifica se bateu a meta baseado na Polaridade"""
    try:
        meta = row['Meta_Num']
        real = row['Resultado_Num']
        polaridade = row['Polaridade']
        
        if polaridade == 1:   # Maior é Melhor (Ex: Produtividade)
            return real >= meta
        elif polaridade == -1: # Menor é Melhor (Ex: Taxa de Congestionamento)
            return real <= meta
        else:
            return real >= meta # Fallback
    except:
        return False

# ==============================================================================
# 4. BARRA LATERAL (FILTROS)
# ==============================================================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center; color:{CORES['primaria']}'>Filtros</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not df.empty:
        # 1. Filtro Ano (Invertido para mostrar o mais recente primeiro)
        anos_disponiveis = sorted(df['Ano'].unique(), reverse=True)
        sel_ano = st.selectbox("Selecione o Ano:", anos_disponiveis)
        
        # 2. Filtro Quadrimestre (Dinâmico baseado no ano)
        quads_do_ano = sorted(df[df['Ano'] == sel_ano]['Quadrimestre'].unique())
        # Tenta pegar o último quadrimestre disponível como padrão
        idx_quad = len(quads_do_ano) - 1
        sel_quad = st.selectbox("Quadrimestre de Referência:", quads_do_ano, index=idx_quad)
        
        st.markdown("---")
        
        # 3. Filtro Unidade
        unidades_disp = sorted(df['Unidade'].dropna().unique())
        sel_unidade = st.multiselect("Filtrar Unidade(s):", unidades_disp, default=unidades_disp)
        
        # 4. Filtro Indicador (Opcional)
        if sel_unidade:
            df_temp = df[df['Unidade'].isin(sel_unidade)]
            ind_disp = sorted(df_temp['Indicador'].unique())
        else:
            ind_disp = []
        sel_indicador = st.multiselect("Filtrar Indicador(es):", ind_disp, default=[])
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 ATUALIZAR DADOS"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    if st.button("🚪 SAIR"):
        st.session_state["logado"] = False
        st.rerun()

# ==============================================================================
# 5. CORPO DO DASHBOARD
# ==============================================================================

# Filtra o DataFrame Globalmente
# Se nenhum indicador for selecionado, mostra todos das unidades selecionadas
filtro_ind = sel_indicador if sel_indicador else df['Indicador'].unique()

df_filtered = df[
    (df['Unidade'].isin(sel_unidade)) & 
    (df['Indicador'].isin(filtro_ind))
].copy()

st.title(f"Painel Estratégico {sel_ano}")

# Abas de Navegação
tab1, tab2 = st.tabs(["📊 VISÃO GRÁFICA", "📋 RELATÓRIO DETALHADO"])

# --- ABA 1: GRÁFICOS ---
with tab1:
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # A. CARDS DE KPI (Topo)
        # Filtra apenas o quadrimestre selecionado para calcular os totais
        df_kpi = df_filtered[
            (df_filtered['Ano'] == sel_ano) & 
            (df_filtered['Quadrimestre'] == sel_quad)
        ].copy()
        
        total_kpi = len(df_kpi)
        if total_kpi > 0:
            sucesso_kpi = df_kpi.apply(check_meta, axis=1).sum()
            falha_kpi = total_kpi - sucesso_kpi
            taxa_sucesso = (sucesso_kpi / total_kpi) * 100
        else:
            sucesso_kpi, falha_kpi, taxa_sucesso = 0, 0, 0
            
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Indicadores ({sel_quad}º Quad)", total_kpi)
        c2.metric("Metas Batidas", int(sucesso_kpi))
        c3.metric("Não Batidas", int(falha_kpi), delta_color="inverse")
        c4.metric("Taxa de Sucesso", f"{taxa_sucesso:.1f}%")
        
        st.markdown("---")
        
        # B. GRADE DE GRÁFICOS (Evolução Histórica)
        # Vamos iterar pelos indicadores filtrados
        indicadores_unicos = sorted(df_filtered['Chave'].unique())
        
        # Loop para criar 2 colunas de gráficos
        for i in range(0, len(indicadores_unicos), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(indicadores_unicos):
                    chave_atual = indicadores_unicos[i+j]
                    
                    with cols[j]:
                        # Pega TODO o histórico desse indicador para montar o gráfico
                        dado_plot = df_filtered[df_filtered['Chave'] == chave_atual].sort_values(['Ano', 'Quadrimestre'])
                        
                        if not dado_plot.empty:
                            # Pega infos estáticas do indicador (Nome, Unidade, etc)
                            row_info = dado_plot.iloc[-1]
                            nome_ind = row_info['Indicador']
                            unidade_nm = row_info['Unidade']
                            polaridade = row_info['Polaridade']
                            
                            # Tenta pegar a Meta do período selecionado para desenhar a linha
                            # Se não tiver meta nesse ano, pega a última disponível
                            meta_row = dado_plot[(dado_plot['Ano'] == sel_ano) & (dado_plot['Quadrimestre'] == sel_quad)]
                            if not meta_row.empty:
                                meta_atual = meta_row['Meta_Num'].values[0]
                            else:
                                meta_atual = row_info['Meta_Num']

                            # Define cores das barras (Verde se bateu, Vermelho se não)
                            cores = [CORES['sucesso'] if check_meta(r) else CORES['atencao'] for _, r in dado_plot.iterrows()]
                            # Textos formatados nas barras
                            textos = [formatar_valor(r['Resultado_Num']) for _, r in dado_plot.iterrows()]

                            # --- PLOTLY CHART ---
                            with st.container():
                                st.markdown(f"<div style='background:white; padding:10px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:15px;'>", unsafe_allow_html=True)
                                
                                fig = go.Figure()
                                
                                # 1. Barras de Resultado
                                fig.add_trace(go.Bar(
                                    x=dado_plot['Periodo_Grafico'],
                                    y=dado_plot['Resultado_Num'],
                                    marker_color=cores,
                                    text=textos,
                                    textposition='auto',
                                    name="Resultado"
                                ))
                                
                                # 2. Linha da Meta (Pontilhada)
                                fig.add_shape(type="line",
                                    x0=-0.5, x1=len(dado_plot)-0.5,
                                    y0=meta_atual, y1=meta_atual,
                                    line=dict(color=CORES['meta_linha'], width=2, dash="dash")
                                )
                                
                                # 3. Anotação da Meta e Polaridade
                                seta = "⬆️ Maior é Melhor" if polaridade == 1 else "⬇️ Menor é Melhor"
                                fig.add_annotation(
                                    x=len(dado_plot)-0.5, y=meta_atual,
                                    text=f" META: {formatar_valor(meta_atual)} ",
                                    showarrow=False, xanchor="right", yshift=10,
                                    font=dict(color=CORES['meta_linha'], size=12, weight="bold"),
                                    bgcolor="rgba(255,255,255,0.8)"
                                )
                                
                                # Layout do Gráfico
                                fig.update_layout(
                                    title=dict(
                                        text=f"<b>{nome_ind}</b><br><span style='font-size:13px;color:#555'>{unidade_nm} | {seta}</span>",
                                        font=dict(size=16, color=CORES['primaria'])
                                    ),
                                    height=300,
                                    margin=dict(l=10, r=10, t=60, b=10),
                                    template="plotly_white",
                                    yaxis=dict(showgrid=True, gridcolor='#eee')
                                )
                                
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                                st.markdown("</div>", unsafe_allow_html=True)


# --- ABA 2: RELATÓRIO ---
with tab2:
    st.markdown(f"<h3 style='color:{CORES['primaria']}'>Relatório Detalhado - {sel_ano}.{sel_quad}</h3>", unsafe_allow_html=True)
    
    # Filtra dados apenas do período selecionado
    df_relatorio = df_filtered[
        (df_filtered['Ano'] == sel_ano) & 
        (df_filtered['Quadrimestre'] == sel_quad)
    ].copy()
    
    if df_relatorio.empty:
        st.info("Não há dados lançados para este período específico.")
    else:
        # Listas para separar visualmente
        lst_ok, lst_nok = [], []
        
        for _, row in df_relatorio.iterrows():
            ind = row['Indicador']
            unid = row['Unidade']
            res = formatar_valor(row['Resultado_Num'])
            meta = formatar_valor(row['Meta_Num'])
            
            # HTML do Cartão
            html_card = f"""
            <div style='font-weight:bold; color:{CORES['texto']}'>{ind}</div>
            <div style='font-size:0.85rem; color:#666; margin-bottom:5px;'>👤 {unid}</div>
            <div style='font-size:1.1rem;'>
                <b>Resultado: {res}</b> <span style='color:#888; font-size:0.9rem'>(Meta: {meta})</span>
            </div>
            """
            
            if check_meta(row):
                lst_ok.append(html_card)
            else:
                lst_nok.append(html_card)
        
        # Colunas de exibição
        col_ok, col_nok = st.columns(2)
        
        with col_ok:
            st.markdown(f"""
            <div style='background-color:{CORES['sucesso_bg']}; color:{CORES['sucesso_txt']}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-bottom:10px;'>
                ✅ METAS BATIDAS ({len(lst_ok)})
            </div>""", unsafe_allow_html=True)
            
            for item in lst_ok:
                st.markdown(f"<div style='background:white; padding:15px; border-radius:8px; border-left:5px solid {CORES['sucesso']}; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:10px;'>{item}</div>", unsafe_allow_html=True)
                
        with col_nok:
            st.markdown(f"""
            <div style='background-color:{CORES['falha_bg']}; color:{CORES['falha_txt']}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-bottom:10px;'>
                ⚠️ NÃO BATIDAS ({len(lst_nok)})
            </div>""", unsafe_allow_html=True)
            
            for item in lst_nok:
                st.markdown(f"<div style='background:white; padding:15px; border-radius:8px; border-left:5px solid {CORES['atencao']}; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:10px;'>{item}</div>", unsafe_allow_html=True)
