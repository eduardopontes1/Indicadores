pip install pandas plotly gspread oauth2client
pip install streamlit pandas plotly gspread-pandas

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TRE-CE Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1Fvo48kFkoTdR9vacDjdasrh6s2MBxcGGFiS53EZcjb8"
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url_csv)
        df.columns = df.columns.str.strip()
        
        # --- TRATAMENTO DE ERROS DE DADOS ---
        # 1. Remove linhas onde o Gestor ou Indicador estão totalmente vazios
        df = df.dropna(subset=['Gestor', 'Indicador', 'Quad'])
        
        # 2. Garante que tudo na coluna Gestor seja Texto (corrige o seu erro do sorted)
        df['Gestor'] = df['Gestor'].astype(str)
        df['Quad'] = df['Quad'].astype(str)
        
        # 3. Garante que Meta e Valor sejam números (converte erros em 0)
        df['Meta'] = pd.to_numeric(df['Meta'], errors='coerce').fillna(0)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR ---
    st.sidebar.title("📌 Filtros Estratégicos")
    
    # Agora o sorted funciona porque garantimos que tudo é string
    lista_gestores = sorted(df['Gestor'].unique())
    gestores = st.sidebar.multiselect("Selecione os Gestores", options=lista_gestores, default=lista_gestores)
    
    lista_quads = sorted(df['Quad'].unique(), reverse=True)
    anos = st.sidebar.multiselect("Períodos", options=lista_quads, default=lista_quads[0] if lista_quads else None)

    # Filtragem
    df_filtered = df[(df['Gestor'].isin(gestores)) & (df['Quad'].isin(anos))].copy()

    # --- KPIs ---
    st.title("📊 Monitoramento de Metas TRE-CE")
    
    if not df_filtered.empty:
        def check_meta(row):
            if row['Sentido'] == 'Superar Meta (>=)':
                return row['Valor'] >= row['Meta']
            return row['Valor'] <= row['Meta']

        df_filtered['Sucesso'] = df_filtered.apply(check_meta, axis=1)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Indicadores", len(df_filtered))
        with col2:
            st.metric("Metas Batidas", int(df_filtered['Sucesso'].sum()))
        with col3:
            falhas = len(df_filtered) - df_filtered['Sucesso'].sum()
            st.metric("Pendentes", int(falhas), delta=f"-{int(falhas)}" if falhas > 0 else "0", delta_color="inverse")

        st.divider()

        # --- GRÁFICOS ---
        df_historico = df[df['Gestor'].isin(gestores)].copy()
        df_historico['Sucesso'] = df_historico.apply(check_meta, axis=1)
        df_historico['Chave'] = df_historico['Gestor'] + " | " + df_historico['Indicador']

        for chave in sorted(df_historico['Chave'].unique()):
            data_plot = df_historico[df_historico['Chave'] == chave].sort_values('Quad')
            
            with st.container():
                st.subheader(f"📈 {chave}")
                fig = go.Figure()
                
                colors = ['#27ae60' if s else '#e67e22' for s in data_plot['Sucesso']]
                
                fig.add_trace(go.Bar(
                    x=data_plot['Quad'], y=data_plot['Valor'],
                    marker_color=colors, text=data_plot['Valor'],
                    textposition='auto', name="Realizado"
                ))
                
                meta_val = data_plot['Meta'].iloc[0]
                fig.add_shape(type="line", x0=-0.5, x1=len(data_plot)-0.5, y0=meta_val, y1=meta_val,
                              line=dict(color="Red", width=3, dash="dash"))
                
                fig.update_layout(height=300, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Selecione ao menos um Gestor e um Período.")
else:
    st.error("Dados não encontrados. Verifique a planilha.")
