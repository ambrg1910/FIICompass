# app.py (versão Final e Definitiva)

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- Configurações da página e CSS ---
st.set_page_config(page_title="FII Compass", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        body, .stApp { font-family: 'Inter', sans-serif; background-color: #F8F9FA; }
        .st-emotion-cache-16txtl3 { padding: 2rem 5rem; }
        .stTabs [role="tablist"] { justify-content: center; border-bottom: 2px solid #EAEAEA; }
        .stTabs [role="tab"][aria-selected="true"] { color: #003366; border-bottom: 2px solid #003366; }
        .card { background-color: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- Funções de carregamento ---
@st.cache_data # Cacheia o dataframe para performance
def load_data():
    try: return pd.read_csv('fiis_data.csv')
    except FileNotFoundError: return None

@st.cache_data(ttl=3600) # Cache do histórico por 1h
def get_history(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        prices = fii.history(period="1y")['Close']
        dividends = fii.dividends
        # Filtra dividendos para o último ano de forma segura
        one_year_ago = datetime.now() - pd.DateOffset(years=1)
        if dividends.index.tz is not None:
             one_year_ago = pd.to_datetime(one_year_ago).tz_localize(dividends.index.tz)
        return prices, dividends[dividends.index > one_year_ago]
    except: return None, None

def plot_chart(df, title, y_axis_title):
    fig = go.Figure(go.Scatter(x=df.index, y=df.values, mode='lines', line=dict(color='#003366', width=2.5)))
    fig.update_layout(title=dict(text=title, x=0.5), yaxis_title=y_axis_title, xaxis_title="", template='plotly_white', height=300, margin=dict(t=50, b=0, l=0, r=0))
    return fig

# --- Cabeçalho e carregamento dos dados ---
st.markdown("<div style='text-align: center;'><h2>🧭 FII Compass</h2><p><i>Seu guia no mundo dos FIIs</i></p></div>", unsafe_allow_html=True)
df = load_data()

if df is not None:
    tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada & Raio-X"])
    
    with tab1:
        with st.container():
            st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs. Ordene pelas colunas para encontrar os ativos que se encaixam na sua estratégia.</p></div>", unsafe_allow_html=True)
            st.dataframe(df.style.format({'Preço Atual':'R$ {:.2f}', 'DY (12M)':'{:.2f}%', 'Liquidez Diária':'R$ {:,.0f}', 'Compass Score': '{:.0f} ⭐'}), use_container_width=True, height=600)

    with tab2:
        with st.container():
            st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione FIIs para uma análise profunda e compare o histórico lado a lado.</p></div>", unsafe_allow_html=True)
            
            fiis_list = sorted(df['Ticker'].tolist())
            selected_fiis = st.multiselect("Selecione os FIIs:", options=fiis_list, default=['BTLG11', 'MXRF11'])

            if selected_fiis:
                df_selected = df[df["Ticker"].isin(selected_fiis)]
                st.dataframe(df_selected.style.format({'Preço Atual':'R$ {:.2f}', 'DY (12M)':'{:.2f}%', 'Liquidez Diária':'R$ {:,.0f}', 'Compass Score': '{:.0f} ⭐'}), use_container_width=True, hide_index=True)

                for ticker in selected_fiis:
                    with st.expander(f"{ticker} - Análise Histórica"):
                        prices, dividends = get_history(ticker)
                        col1, col2 = st.columns(2)
                        with col1:
                            if prices is not None: st.plotly_chart(plot_chart(prices, "Histórico de Preço (1 Ano)", "Preço (R$)"), use_container_width=True)
                            else: st.warning("Não foi possível carregar o histórico de preços.")
                        with col2:
                            if dividends is not None and not dividends.empty: st.plotly_chart(plot_chart(dividends, "Histórico de Dividendos (1 Ano)", "Dividendo (R$)"), use_container_width=True)
                            else: st.info("Sem histórico de dividendos no período.")
else:
    st.error("ERRO: Arquivo `fiis_data.csv` não encontrado. Por favor, rode o script `update_data.py` localmente e envie o arquivo para o GitHub.")
