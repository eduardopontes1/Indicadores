import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import numpy as np

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(
    page_title="Painel Estratégico | TRE-CE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta de Cores Institucional (Adaptada)
CORES = {
    "primaria": "#0c2461",         # Azul Escuro Profundo
    "secundaria": "#4a69bd",       # Azul Médio
    "destaque": "#4682B4",         # SteelBlue
    "meta_linha": "#e55039",       # Vermelho Tomate (Linha da meta)
    "texto": "#2C3E50",            # Cinza Escuro
    "fundo": "#F4F6F9",            # Cinza Claro Fundo
    "sucesso": "#20bf6b",          # Verde Vibrante
    "atencao": "#eb3b5a",          # Vermelho Vibrante
    "sucesso_bg": "#d1f2eb", "sucesso_txt": "#0e6655",
    "falha_bg": "#fadbd8",   "falha_txt": "#78281f"
}

# CSS Personalizado
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif !important;
        background-color: {CORES['fundo']};
        color: {CORES['texto']};
    }}
    
    /* Cabeçalhos */
    h1 {{ color: {CORES['primaria']}; font-weight: 800 !important; }}
    h3 {{ color: {CORES['secundaria']}; font-weight: 700 !important; }}
    
    /* Métricas (Cards do Topo) */
    div[data-testid="stMetric"] {{
        background-color: white;
        border-top: 5px solid {CORES['primaria']};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* Botões */
    div.stButton > button {{
        width: 100%;
        background-color: {CORES['primaria']};
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }}
    div.stButton > button:hover {{
        background-color: {CORES['secundaria']};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE LOGIN
# ==============================================================================
USUARIOS = {
    "admin": "admin",      # Senha simples para teste
    "TRE-CE": "TReCe.2026",
    "eduardo": "123"
}

def verificar_login():
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if not st.session_state["logado"]:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            with st.container():
                st.markdown(
                    f"""
                    <div style='background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;'>
                        <h1 style='color: {CORES['primaria']}; margin-bottom: 0;'>🔐 Acesso Restrito</h1>
                        <p style='color: #666; font-size: 1.1rem;'>Painel de Monitoramento Estratégico</p>
                    </div>
                    <br>
                    """, 
                    unsafe_allow_html=True
                )
                usuario = st.text_input("Usuário", placeholder="Digite seu usuário...")
                senha = st.text_input("Senha", type="password", placeholder="Digite sua senha...")
                
                if st.button("ENTRAR NO SISTEMA"):
                    if usuario in USUARIOS and USUARIOS[usuario] == senha:
                        st.session_state["logado"] = True
                        st.success("Acesso autorizado! Carregando...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
        st.stop()

verificar_login()

# ==============================================================================
# 3. MOTOR DE DADOS (LOAD DATA)
# ==============================================================================
@st.cache_data(ttl=60)
def load_data():
    """
    Carrega os dados.
    Para usar Link: Substitua 'dados_simulados.csv' pela URL do Gist ou Google Sheets.
    """
    
    # --- CONFIGURAÇÃO DA FONTE DE DADOS ---
    # Opção A: Arquivo Local (Se estiver na mesma pasta)
    #arquivo = "dados_simulados.csv" 
    
    # Opção B: Link da Web (Descomente e coloque seu link abaixo se for usar online)
     arquivo = "https://docs.google.com/spreadsheets/d/1oefuUAE4Vlt9WLecgS0_4ZZZvAfV_c-t5M6nT3YOMjs/edit?usp=sharing"
    
    try:
        # Lê o CSV (assumindo separador padrão de vírgula)
        df = pd.read_csv(arquivo)
        
        # 1. Padronização de Colunas
        df.columns = df.columns.str.strip()
        
        # 2. Tratamento de Tipos Numéricos
        # Removemos linhas que não tenham números válidos na Meta ou Resultado
        df = df.dropna(subset=['Meta_Num', 'Resultado_Num'])
        
        # 3. Tratamento de Polaridade
        if 'Polaridade' in df.columns:
            df['Polaridade'] = pd.to_numeric(df['Polaridade'], errors='coerce').fillna(1)
        else:
            df['Polaridade'] = 1 # Assume Maior é Melhor se não tiver a coluna

        # 4. Criação de Colunas Temporais para Ordenação
        # Removemos ".0" caso o ano tenha vindo como float (ex: 2022.0 -> 2022)
        df['Ano'] = df['Ano'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['Quadrimestre'] = df['Quadrimestre'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Coluna auxiliar para o eixo X do gráfico (Ex: "2023.1", "2023.2")
        df['Periodo_Grafico'] = df['Ano'] + "." + df['Quadrimestre']
        
        # 5. Criar Chave Única (Unidade + Indicador) para facilitar loops
        df['Chave'] = df['Unidade'] + " - " + df['Indicador']
        
        return df

    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados. Verifique se o arquivo '{arquivo}' existe ou se o link está correto.")
        st.error(f"Detalhe do erro: {e}")
        return pd.DataFrame()

df = load_data()

# --- FUNÇÕES AUXILIARES ---

def formatar_valor(valor):
    """Formata números para o padrão brasileiro (vírgula decimal)"""
    try:
        if pd.isna(valor): return "-"
        if valor >= 1000:
            return f"{valor:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elif isinstance(valor, float):
            return f"{valor:.2f}".replace('.', ',')
        return str(valor)
    except:
        return str(valor)

def check_meta(row):
    """
    Verifica se a meta foi batida considerando a Polaridade.
    Polaridade  1: Resultado >= Meta (Ex: Produtividade)
    Polaridade -1: Resultado <= Meta (Ex: Taxa de Congestionamento)
    """
    try:
        meta = float(row['Meta_Num'])
        real = float(row['Resultado_Num'])
        polaridade = int(row['Polaridade'])
        
        if polaridade == 1:
            return real >= meta
        elif polaridade == -1:
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
        # 1. Filtro de Ano (Ordenado do mais recente para o mais antigo)
        anos_disponiveis = sorted(df['Ano'].unique(), reverse=True)
        sel_ano = st.selectbox("📅 Selecione o Ano:", anos_disponiveis)
        
        # 2. Filtro de Quadrimestre (Apenas os existentes no ano selecionado)
        quads_do_ano = sorted(df[df['Ano'] == sel_ano]['Quadrimestre'].unique())
        idx_padrao = len(quads_do_ano) - 1 # Tenta pegar o último
        sel_quad = st.selectbox("📆 Quadrimestre de Referência:", quads_do_ano, index=idx_padrao)
        
        st.markdown("---")
        
        # 3. Filtro de Unidade
        unidades_disp = sorted(df['Unidade'].unique())
        sel_unidade = st.multiselect("🏢 Filtrar Unidade(s):", unidades_disp, default=unidades_disp)
        
        # 4. Filtro de Indicador (Condicionado às unidades)
        if sel_unidade:
            df_temp = df[df['Unidade'].isin(sel_unidade)]
            ind_disp = sorted(df_temp['Indicador'].unique())
        else:
            ind_disp = []
            
        sel_indicador = st.multiselect("🎯 Filtrar Indicador(es):", ind_disp)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 ATUALIZAR DADOS"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    if st.button("🚪 LOGOUT"):
        st.session_state["logado"] = False
        st.rerun()

# ==============================================================================
# 5. CORPO DO DASHBOARD
# ==============================================================================

# Se o usuário não selecionou indicadores, assume todos das unidades filtradas
lista_indicadores = sel_indicador if sel_indicador else df['Indicador'].unique()

# Filtro Principal do DataFrame
df_filtered = df[
    (df['Unidade'].isin(sel_unidade)) & 
    (df['Indicador'].isin(lista_indicadores))
].copy()

# Título Dinâmico
st.title(f"Painel Estratégico {sel_ano}")
st.markdown(f"**Referência:** {sel_quad}º Quadrimestre")

# Abas
tab1, tab2 = st.tabs(["📊 VISÃO ESTRATÉGICA", "📋 RELATÓRIO DETALHADO"])

# --- ABA 1: GRÁFICOS ---
with tab1:
    if df_filtered.empty:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
    else:
        # A. MÉTRICAS KPI (Topo)
        # Filtra apenas o momento atual (Ano/Quad selecionado)
        df_kpi = df_filtered[
            (df_filtered['Ano'] == sel_ano) & 
            (df_filtered['Quadrimestre'] == sel_quad)
        ].copy()
        
        total = len(df_kpi)
        
        if total > 0:
            sucesso = df_kpi.apply(check_meta, axis=1).sum()
            falha = total - sucesso
            taxa = (sucesso / total) * 100
        else:
            sucesso, falha, taxa = 0, 0, 0
            
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total de Indicadores", total)
        k2.metric("Metas Batidas", int(sucesso))
        k3.metric("Não Batidas", int(falha), delta_color="inverse")
        k4.metric("Taxa de Sucesso", f"{taxa:.1f}%")
        
        st.markdown("---")
        
        # B. VISUALIZAÇÃO GRÁFICA (Grid 2 colunas)
        # Lista única de chaves (Indicador + Unidade) para iterar
        chaves_unicas = sorted(df_filtered['Chave'].unique())
        
        for i in range(0, len(chaves_unicas), 2):
            cols = st.columns(2)
            
            # Loop interno para preencher as 2 colunas
            for j in range(2):
                if i + j < len(chaves_unicas):
                    chave_atual = chaves_unicas[i+j]
                    
                    with cols[j]:
                        # Pega TODO o histórico desse indicador (para mostrar evolução)
                        dado_plot = df_filtered[df_filtered['Chave'] == chave_atual].sort_values(['Periodo_Grafico'])
                        
                        if not dado_plot.empty:
                            # Dados cadastrais do indicador
                            row_info = dado_plot.iloc[-1]
                            nome_ind = row_info['Indicador']
                            unidade_nm = row_info['Unidade']
                            polaridade = row_info['Polaridade']
                            
                            # Tenta pegar a meta do período selecionado para desenhar a linha de referência
                            meta_ref = dado_plot[
                                (dado_plot['Ano'] == sel_ano) & 
                                (dado_plot['Quadrimestre'] == sel_quad)
                            ]
                            
                            # Se tiver meta no período atual, usa ela. Senão, usa a última disponível.
                            if not meta_ref.empty:
                                valor_meta_linha = meta_ref['Meta_Num'].values[0]
                            else:
                                valor_meta_linha = row_info['Meta_Num']

                            # Cores das barras (Dinâmicas)
                            cores = [CORES['sucesso'] if check_meta(r) else CORES['atencao'] for _, r in dado_plot.iterrows()]
                            
                            # Textos das barras
                            textos = [formatar_valor(r['Resultado_Num']) for _, r in dado_plot.iterrows()]

                            # --- CRIAÇÃO DO GRÁFICO PLOTLY ---
                            with st.container():
                                st.markdown(f"<div style='background:white; padding:10px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:20px;'>", unsafe_allow_html=True)
                                
                                fig = go.Figure()
                                
                                # Barras
                                fig.add_trace(go.Bar(
                                    x=dado_plot['Periodo_Grafico'],
                                    y=dado_plot['Resultado_Num'],
                                    marker_color=cores,
                                    text=textos,
                                    textposition='auto',
                                    name="Resultado"
                                ))
                                
                                # Linha da Meta
                                fig.add_shape(type="line",
                                    x0=-0.5, x1=len(dado_plot)-0.5,
                                    y0=valor_meta_linha, y1=valor_meta_linha,
                                    line=dict(color=CORES['meta_linha'], width=3, dash="dash")
                                )
                                
                                # Anotação de Meta e Polaridade
                                simbolo = "⬆️ Maior é Melhor" if polaridade == 1 else "⬇️ Menor é Melhor"
                                fig.add_annotation(
                                    x=len(dado_plot)-0.5, y=valor_meta_linha,
                                    text=f" META: {formatar_valor(valor_meta_linha)} ",
                                    showarrow=False, xanchor="right", yshift=10,
                                    font=dict(color=CORES['meta_linha'], size=12, weight="bold"),
                                    bgcolor="rgba(255,255,255,0.8)"
                                )
                                
                                # Layout
                                fig.update_layout(
                                    title=dict(
                                        text=f"<b>{nome_ind}</b><br><span style='font-size:13px;color:#555'>{unidade_nm} | {simbolo}</span>",
                                        font=dict(size=16, color=CORES['primaria'])
                                    ),
                                    height=320,
                                    margin=dict(l=10, r=10, t=70, b=10),
                                    template="plotly_white",
                                    yaxis=dict(showgrid=True, gridcolor='#eee'),
                                    xaxis=dict(showgrid=False)
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
        st.info(f"Não há lançamentos de dados para o {sel_quad}º Quadrimestre de {sel_ano}.")
    else:
        # Separa em listas OK e NOK
        lst_ok, lst_nok = [], []
        
        for _, row in df_relatorio.iterrows():
            # Monta o HTML do Card
            html_card = f"""
            <div style='font-weight:bold; color:{CORES['texto']}'>{row['Indicador']}</div>
            <div style='font-size:0.85rem; color:#666; margin-bottom:5px;'>👤 {row['Unidade']}</div>
            <div style='font-size:1.1rem;'>
                <b>Resultado: {formatar_valor(row['Resultado_Num'])}</b> 
                <span style='color:#888; font-size:0.9rem'>(Meta: {formatar_valor(row['Meta_Num'])})</span>
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
            <div style='background-color:{CORES['sucesso_bg']}; color:{CORES['sucesso_txt']}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-bottom:10px; border: 1px solid {CORES['sucesso']}'>
                ✅ METAS BATIDAS ({len(lst_ok)})
            </div>""", unsafe_allow_html=True)
            
            for item in lst_ok:
                st.markdown(f"<div style='background:white; padding:15px; border-radius:8px; border-left:5px solid {CORES['sucesso']}; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:10px;'>{item}</div>", unsafe_allow_html=True)
                
        with col_nok:
            st.markdown(f"""
            <div style='background-color:{CORES['falha_bg']}; color:{CORES['falha_txt']}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-bottom:10px; border: 1px solid {CORES['atencao']}'>
                ⚠️ NÃO BATIDAS ({len(lst_nok)})
            </div>""", unsafe_allow_html=True)
            
            for item in lst_nok:
                st.markdown(f"<div style='background:white; padding:15px; border-radius:8px; border-left:5px solid {CORES['atencao']}; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:10px;'>{item}</div>", unsafe_allow_html=True)
