import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO VISUAL E CSS PROFISSIONAL ---
st.set_page_config(
    page_title="Painel Estratégico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cores baseadas nas imagens de referência
CORES = {
    "verde_sucesso": "#00a65a",    # Verde sólido forte
    "amarelo_atencao": "#f1c40f",  # Amarelo/Dourado
    "meta_linha": "#d35400",       # Laranja escuro/Dourado para a linha
    "texto_escuro": "#2c3e50",
    "texto_claro": "#ffffff",
    "fundo_pag": "#ecf0f5",        # Cinza claro corporativo
    "fundo_card": "#ffffff"
}

# CSS para forçar fonte Montserrat, tamanhos maiores e remover estilo padrão
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        color: {CORES['texto_escuro']};
        background-color: {CORES['fundo_pag']};
    }}

    /* Aumentando títulos */
    h1 {{ font-size: 2.2rem !important; font-weight: 700 !important; }}
    h2 {{ font-size: 1.8rem !important; font-weight: 600 !important; }}
    h3 {{ font-size: 1.4rem !important; font-weight: 600 !important; }}

    /* Estilo dos filtros multiselect */
    .stMultiSelect label {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }}

    /* Estilo das caixas de mensagem (Bateu/Não bateu) */
    .status-box-success {{
        background-color: #dff0d8;
        border-left: 5px solid {CORES['verde_sucesso']};
        padding: 15px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 1.1rem;
        color: #3c763d;
    }}
    .status-box-fail {{
        background-color: #fcf8e3;
        border-left: 5px solid {CORES['amarelo_atencao']};
        padding: 15px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 1.1rem;
        color: #8a6d3b;
    }}
    
    /* Ajuste fino no container principal */
    .block-container {{ padding-top: 1rem; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARREGAMENTO DE DADOS (ROBUSTO) ---
@st.cache_data(ttl=60)
def load_data():
    # SUBSTITUA PELO SEU ID CORRETO SE MUDOU
    sheet_id = "1Fvo48kFkoTdR9vacDjdasrh6s2MBxcGGFiS53EZcjb8"
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    try:
        df = pd.read_csv(url_csv)
        df.columns = df.columns.str.strip()
        
        cols_map = {'Semestre': 'Quad', 'Periodo': 'Quad', 'Período': 'Quad'}
        df = df.rename(columns=lambda x: cols_map.get(x, x))

        # Verifica colunas essenciais
        required_cols = ['Gestor', 'Indicador', 'Quad', 'Meta', 'Valor', 'Sentido']
        if not all(col in df.columns for col in required_cols):
            st.error(f"A planilha precisa ter as colunas: {', '.join(required_cols)}")
            return pd.DataFrame()

        df = df.dropna(subset=['Gestor', 'Indicador', 'Quad'])
        df['Gestor'] = df['Gestor'].astype(str)
        df['Indicador'] = df['Indicador'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        
        # Garante que Macro existe
        if 'Macro' not in df.columns: df['Macro'] = 'Geral'
        df['Macro'] = df['Macro'].astype(str)

        for col in ['Meta', 'Valor']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

df = load_data()

# Função para verificar meta
def check_meta(row):
    try:
        meta, valor = float(row['Meta']), float(row['Valor'])
        sentido = str(row.get('Sentido', '')).lower()
        if 'superar' in sentido or '>=' in sentido: return valor >= meta
        elif 'manter' in sentido or '<=' in sentido: return valor <= meta
        return valor >= meta # Default
    except: return False

# --- 3. BARRA LATERAL (FILTROS AVANÇADOS) ---
with st.sidebar:
    st.header("Filtros de Visualização")
    st.write("Use as caixas para pesquisar ou selecionar.")
    st.markdown("---")
    
    if not df.empty:
        # 3.1. Seletor do Quadrimestre de Referência (FOCO)
        quads_unicos = sorted(df['Quad'].unique())
        # Tenta pegar o último como padrão
        quad_padrao_idx = len(quads_unicos) - 1 if quads_unicos else 0
        quad_referencia = st.selectbox(
            "Quadrimestre de Referência (Foco da Análise):",
            quads_unicos,
            index=quad_padrao_idx,
            help="A mensagem de 'Bateu/Não Bateu' será baseada neste período."
        )
        st.markdown("---")

        # 3.2. Filtros Multiselect (Com pesquisa e "Selecionar Todos" padrão)
        # Macrodesafio
        macros_disp = sorted(df['Macro'].unique())
        sel_macro = st.multiselect("Filtrar Macrodesafio:", macros_disp, default=macros_disp)
        
        # Gestor
        gestores_disp = sorted(df[df['Macro'].isin(sel_macro)]['Gestor'].unique()) if sel_macro else []
        sel_gestor = st.multiselect("Filtrar Gestão (Gestor):", gestores_disp, default=gestores_disp)
        
        # Indicador (Opcional, para refinamento)
        filtros_ativos = df['Gestor'].isin(sel_gestor) & df['Macro'].isin(sel_macro)
        indicadores_disp = sorted(df[filtros_ativos]['Indicador'].unique()) if not filtros_ativos.empty else []
        sel_indicador = st.multiselect("Filtrar Indicadores Específicos:", indicadores_disp, default=indicadores_disp)

        # Botão de Atualizar
        st.markdown("---")
        if st.button("Recarregar Dados da Planilha", type="primary"):
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("Sem dados para carregar filtros.")
        st.stop()

# --- 4. CORPO PRINCIPAL (ABAS) ---

# Filtragem Global
df_filtered = df[
    (df['Gestor'].isin(sel_gestor)) & 
    (df['Macro'].isin(sel_macro)) &
    (df['Indicador'].isin(sel_indicador))
].copy()

st.title("Painel de Monitoramento Estratégico")

# Criação das Abas
tab_graficos, tab_relatorio = st.tabs(["📊 Painel Gráfico Detalhado", "📑 Relatório Gerencial (Listas)"])

# --- ABA 1: GRÁFICOS ---
with tab_graficos:
    if df_filtered.empty:
        st.warning("⚠️ Nenhum indicador selecionado. Por favor, marque as opções nos filtros laterais.")
    else:
        st.write(f"Visualizando histórico completo. Análise de meta focada em: **{quad_referencia}**")
        st.markdown("---")

        # Agrupa por chave única para gerar um gráfico por indicador
        df_filtered['ChaveUnica'] = df_filtered['Macro'] + " | " + df_filtered['Gestor'] + " | " + df_filtered['Indicador']
        indicadores_unicos = df_filtered['ChaveUnica'].unique()

        for chave in indicadores_unicos:
            # Separa os dados deste indicador específico
            dado_ind = df_filtered[df_filtered['ChaveUnica'] == chave].sort_values('Quad')
            
            # Informações do cabeçalho do gráfico
            macro_atual = dado_ind['Macro'].iloc[0]
            gestor_atual = dado_ind['Gestor'].iloc[0]
            nome_indicador = dado_ind['Indicador'].iloc[0]
            meta_valor = dado_ind['Meta'].iloc[0]
            
            # Determina cores baseado se bateu a meta em cada período histórico
            cores_barras = [CORES['verde_sucesso'] if check_meta(row) else CORES['amarelo_atencao'] for _, row in dado_ind.iterrows()]

            # --- CONSTRUÇÃO DO GRÁFICO PLOTLY (ESTILO REFERÊNCIA) ---
            fig = go.Figure()

            # 1. Adiciona as Barras
            fig.add_trace(go.Bar(
                x=dado_ind['Quad'],
                y=dado_ind['Valor'],
                marker_color=cores_barras,
                text=dado_ind['Valor'], # Valor dentro da barra
                textposition='auto',
                textfont=dict(color='white', size=14, weight='bold'), # Texto branco e negrito
                name='Resultado',
                hoverinfo='x+y+text'
            ))

            # 2. Linha da Meta (Pontilhada Dourada com Texto)
            fig.add_shape(
                type="line", line=dict(color=CORES['meta_linha'], width=3, dash="dash"),
                x0=-0.5, x1=len(dado_ind['Quad'])-0.5, y0=meta_valor, y1=meta_valor,
                xref='x', yref='y'
            )
            # Rótulo escrito "META: X" ao lado da linha
            fig.add_annotation(
                x=len(dado_ind['Quad'])-0.5, y=meta_valor,
                text=f"META: {meta_valor}",
                showarrow=False,
                xanchor="right", yanchor="bottom",
                yshift=5,
                font=dict(color=CORES['meta_linha'], size=13, weight="bold")
            )

            # 3. Layout Profissional (Eixos visíveis, fontes grandes)
            fig.update_layout(
                title=dict(
                    text=f"<b>{nome_indicador}</b><br><span style='font-size: 16px; color: gray;'>Macro: {macro_atual} | Gestor: {gestor_atual}</span>",
                    font=dict(size=20, family="Montserrat")
                ),
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(size=14, weight='bold') # Rótulos do eixo X maiores
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='#e0e0e0', gridwidth=1, # Grid horizontal visível
                    tickfont=dict(size=12),
                    zeroline=False
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(t=100, b=40, l=60, r=40),
                showlegend=False
            )

            # Exibe o gráfico em um container branco (estilo card)
            with st.container():
                st.plotly_chart(fig, use_container_width=True)

                # --- LÓGICA DE MENSAGEM DE STATUS (BASEADA NO QUAD DE REFERÊNCIA) ---
                # Tenta encontrar a linha correspondente ao quadrimestre selecionado no filtro
                dado_quad_ref = dado_ind[dado_ind['Quad'] == quad_referencia]
                
                if not dado_quad_ref.empty:
                    # Se tem dados para o quadrimestre de referência
                    row_ref = dado_quad_ref.iloc[0]
                    bateu = check_meta(row_ref)
                    valor_ref = row_ref['Valor']
                    
                    if bateu:
                        msg = f"✅ {quad_referencia.upper()}: META SUPERADA! (Resultado: {valor_ref} vs Meta: {meta_valor})"
                        st.markdown(f'<div class="status-box-success">{msg}</div>', unsafe_allow_html=True)
                    else:
                        msg = f"❌ {quad_referencia.upper()}: NÃO SUPERADA! (Resultado: {valor_ref} vs Meta: {meta_valor})"
                        st.markdown(f'<div class="status-box-fail">{msg}</div>', unsafe_allow_html=True)
                else:
                    # Se não tem dados para o quadrimestre de referência
                    st.info(f"ℹ️ Sem dados lançados para o {quad_referencia} neste indicador.")
            
            st.divider()

# --- ABA 2: RELATÓRIO GERENCIAL ---
with tab_relatorio:
    st.header(f"Relatório Sintético - Foco: {quad_referencia}")
    st.write("Listagem baseada exclusivamente no desempenho do quadrimestre de referência selecionado.")
    st.markdown("---")

    if df_filtered.empty:
         st.warning("Sem dados filtrados para gerar relatório.")
    else:
        # Listas para armazenar os resultados
        bateu_meta = []
        nao_bateu_meta = []
        sem_dados_quad = []

        # Itera sobre os indicadores únicos filtrados
        df_filtered['ChaveSimples'] = df_filtered['Gestor'] + " | " + df_filtered['Indicador']
        for chave in df_filtered['ChaveSimples'].unique():
            # Pega os dados desse indicador
            dado_total_ind = df_filtered[df_filtered['ChaveSimples'] == chave]
            
            # Tenta pegar apenas a linha do quadrimestre de referência
            dado_ref = dado_total_ind[dado_total_ind['Quad'] == quad_referencia]

            if dado_ref.empty:
                sem_dados_quad.append(chave)
            else:
                row = dado_ref.iloc[0]
                if check_meta(row):
                    bateu_meta.append(f"**{row['Gestor']}** | {row['Indicador']} (Res: {row['Valor']})")
                else:
                    nao_bateu_meta.append(f"**{row['Gestor']}** | {row['Indicador']} (Res: {row['Valor']} / Meta: {row['Meta']})")

        # --- EXIBIÇÃO DAS LISTAS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"✅ Bateram a Meta em {quad_referencia}")
            if bateu_meta:
                for item in bateu_meta: st.markdown(f"- {item}")
            else: st.write("Nenhum indicador nesta lista.")
            
            st.write("") # Espaço
            st.subheader("ℹ️ Sem dados neste período")
            if sem_dados_quad:
                for item in sem_dados_quad: st.markdown(f"- {item}")
            else: st.write("Todos os indicadores filtrados possuem dados para este período.")

        with c2:
            st.subheader(f"❌ Não Bateram a Meta em {quad_referencia}")
            if nao_bateu_meta:
                 # Usando um container para destacar a lista de atenção
                with st.container():
                    for item in nao_bateu_meta: 
                        st.markdown(f"- <span style='color:{CORES['meta_linha']}'>{item}</span>", unsafe_allow_html=True)
            else: st.success("Parabéns! Nenhum indicador ficou abaixo da meta neste período.")
