# app.py (versão 11.0 - A Arquitetura Final: Lendo de CSV)

import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="FII Compass Pro", page_icon="🧭", layout="wide")

def load_css():
    st.markdown("""
    <style>
        body { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        .card { background-color: #FFFFFF; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #EAEAEA; }
        h1, h2, h3 { color: #1E293B; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNÇÕES DE CARREGAMENTO (AGORA LOCAIS E RÁPIDAS)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600) # Cache do CSV por 1 hora
def load_data_from_csv():
    """Função para carregar os dados do nosso arquivo local."""
    try:
        df = pd.read_csv('fiis_data.csv')
        return df
    except FileNotFoundError:
        return None

# Funções de busca de histórico para o Raio-X (ainda precisam ser ao vivo)
@st.cache_data(ttl=900)
def get_fii_history_yfinance(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        hist_prices = fii.history(period="1y")
        hist_dividends = fii.dividends
        return hist_prices, hist_dividends
    except: return None, None

def plot_chart(df, title, y_title, hover_template):
    fig = go.Figure(go.Scatter(x=df.index, y=df.values, mode='lines', name=y_title, hovertemplate=hover_template, line=dict(color='#003366', width=2)))
    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=18)), yaxis_title=y_title, xaxis_title="Data", template='plotly_white', height=300, margin=dict(t=50, b=10, l=10, r=10))
    return fig

# -----------------------------------------------------------------------------
# INÍCIO DA EXECUÇÃO DA INTERFACE
# -----------------------------------------------------------------------------
load_css()
st.markdown("<h1 style='text-align: center; color: #1E293B;'>🧭 FII Compass</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4A5568; font-weight: 400;'>Seu Norte no Mundo dos Fundos Imobiliários</h3>", unsafe_allow_html=True)
st.markdown("---")

all_fiis_df = load_data_from_csv()

# ESTRUTURA DE ABAS
tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada e Raio-X"])

with tab1:
    st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs listados. Utilize os filtros e a ordenação nas colunas para encontrar os ativos que se encaixam na sua estratégia.</p></div>", unsafe_allow_html=True)
    if all_fiis_df is not None and not all_fiis_df.empty:
        st.dataframe(all_fiis_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, height=600)
    else:
        st.error("Arquivo de dados 'fiis_data.csv' não encontrado. Execute o script 'update_data.py' para gerar os dados.")

with tab2:
    st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione os FIIs que deseja analisar em profundidade.</p></div>", unsafe_allow_html=True)
    
    if all_fiis_df is not None:
        fiis_selecionados = st.multiselect('Selecione os FIIs para o Raio-X:', options=all_fiis_df['Ticker'].tolist(), default=['BTLG11', 'MXRF11', 'XPML11'])
        
        if fiis_selecionados:
            selected_df = all_fiis_df[all_fiis_df['Ticker'].isin(fiis_selecionados)]
            st.dataframe(selected_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("### 🔬 Raio-X Individual")
            
            for ticker in fiis_selecionados:
                with st.expander(f"**{ticker}** - Análise Histórica"):
                    prices, dividends = get_fii_history_yfinance(ticker)
                    
                    if prices is not None:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_price = plot_chart(prices['Close'], 'Preço (1 Ano)', 'R$', '<b>Data</b>: %{x}<br><b>Preço</b>: R$ %{y:.2f}')
                            st.plotly_chart(fig_price, use_container_width=True)
                        with col2:
                            if dividends is not None and not dividends.empty:
                                # CORREÇÃO DEFINITIVA DO KEYERROR
                                fig_div = plot_chart(dividends, 'Dividendos (1 Ano)', 'R$', '<b>Data</b>: %{x}<br><b>Dividendo</b>: R$ %{y:.2f}')
                                st.plotly_chart(fig_div, use_container_width=True)
                            else:
                                st.info("Sem dividendos registrados para este FII no último ano.")
                    else:
                        st.error(f"Não foi possível buscar o histórico para {ticker}.")
        else:
            st.info("Selecione um ou mais FIIs para iniciar o Raio-X.")

st.markdown("<div style='text-align: center; margin-top: 30px;'><p>FII Compass | Arquitetura Definitiva</p></div>", unsafe_allow_html=True)
