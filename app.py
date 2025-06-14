# app.py (versão 11.0 - Arquitetura Final: Leitura de CSV)

import streamlit as st
import pandas as pd
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
@st.cache_data(ttl=3600)
def load_data_from_csv():
    try:
        return pd.read_csv('fiis_data.csv')
    except FileNotFoundError:
        return None

# Funções de busca de histórico para o Raio-X (a única parte que ainda busca ao vivo)
@st.cache_data(ttl=900)
def get_fii_history_yfinance(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        hist_prices = fii.history(period="1y")
        hist_dividends = fii.dividends
        return hist_prices, hist_dividends
    except:
        return None, None

def plot_chart(df, title, y_title):
    # O df aqui é uma Série do Pandas, com Data no índice e Valor nos valores
    fig = go.Figure(go.Scatter(x=df.index, y=df.values, mode='lines', line=dict(color='#003366', width=2)))
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

# --- Estrutura de Abas ---
tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada e Raio-X"])

with tab1:
    st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs listados.</p></div>", unsafe_allow_html=True)
    if all_fiis_df is not None:
        st.dataframe(all_fiis_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, height=600)
    else:
        st.error("Arquivo de dados 'fiis_data.csv' não encontrado. Por favor, execute o script 'update_data.py' no seu computador e envie o arquivo gerado para o repositório no GitHub.")

with tab2:
    st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione os FIIs que deseja analisar em profundidade.</p></div>", unsafe_allow_html=True)
    if all_fiis_df is not None:
        fiis_selecionados = st.multiselect('Selecione os FIIs para o Raio-X:', options=sorted(all_fiis_df['Ticker'].tolist()), default=['BTLG11', 'MXRF11', 'XPML11'])
        
        if fiis_selecionados:
            selected_df = all_fiis_df[all_fiis_df['Ticker'].isin(fiis_selecionados)]
            st.dataframe(selected_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("### 🔬 Raio-X Individual")
            
            for ticker in fiis_selecionados:
                with st.expander(f"**{ticker}** - Análise Histórica"):
                    prices, dividends = get_fii_history_yfinance(ticker)
                    col1, col2 = st.columns(2)
                    with col1:
                        if prices is not None:
                            fig_price = plot_chart(prices['Close'], 'Preço (1 Ano)', 'R$')
                            st.plotly_chart(fig_price, use_container_width=True)
                        else:
                            st.error(f"Não foi possível buscar o histórico de preços para {ticker}.")
                    with col2:
                        if dividends is not None and not dividends.empty:
                            # CORREÇÃO DEFINITIVA DO KEYERROR 'DIVIDENDS'
                            fig_div = plot_chart(dividends, 'Dividendos (1 Ano)', 'R$')
                            st.plotly_chart(fig_div, use_container_width=True)
                        else:
                            st.info("Sem dividendos registrados para este FII no último ano.")

st.markdown("<div style='text-align: center; margin-top: 30px;'><p>FII Compass | Arquitetura Estável</p></div>", unsafe_allow_html=True)
