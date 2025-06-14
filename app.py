# app.py (versão Final - Arquitetura Estável e Offline-First)

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
        .stDataFrame { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNÇÕES DE CARREGAMENTO
# -----------------------------------------------------------------------------
@st.cache_data # Cacheia o dataframe para performance
def load_data():
    """Carrega os dados pré-processados do arquivo CSV local."""
    try:
        return pd.read_csv('fiis_data.csv')
    except FileNotFoundError:
        return None

# A busca de histórico para o Raio-X ainda é ao vivo, mas tratada de forma segura
@st.cache_data(ttl=900)
def get_history(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        prices = fii.history(period="1y")['Close']
        dividends = fii.dividends
        return prices, dividends
    except:
        return None, None

def plot_chart(df, title, y_axis_title):
    """Renderiza um gráfico limpo e profissional com Plotly."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df.values, mode='lines',
                             line=dict(color='#003366', width=2)))
    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=16)),
                      yaxis_title=y_axis_title, xaxis_title="",
                      template='plotly_white', height=300,
                      margin=dict(t=40, b=20, l=0, r=0))
    return fig

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL DA APLICAÇÃO
# -----------------------------------------------------------------------------
load_css()
st.markdown("<h1 style='text-align: center;'>🧭 FII Compass</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4A5568; font-weight: 400;'>Seu Norte no Mundo dos Fundos Imobiliários</h3>", unsafe_allow_html=True)
st.markdown("---")

df = load_data()

# Verifica se os dados foram carregados antes de construir o resto da interface
if df is not None and not df.empty:
    tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada e Raio-X"])
    
    with tab1:
        st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs. Use a ordenação nas colunas para encontrar os ativos que se encaixam na sua estratégia.</p></div>", unsafe_allow_html=True)
        # Formatação profissional da tabela
        st.dataframe(df.style.format({
            'Preço Atual': 'R$ {:.2f}',
            'DY (12M)': '{:.2f}%',
            'Liquidez Diária': 'R$ {:,.0f}'
        }), use_container_width=True, height=600)
        
    with tab2:
        st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione os FIIs que deseja analisar em profundidade.</p></div>", unsafe_allow_html=True)
        
        fiis_list = sorted(df['Ticker'].tolist())
        default_selection = [fii for fii in ['BTLG11', 'MXRF11', 'XPML11'] if fii in fiis_list]
        fiis_selecionados = st.multiselect('Selecione os FIIs para o Raio-X:', options=fiis_list, default=default_selection)
        
        for ticker in fiis_selecionados:
            with st.expander(f"**{ticker}** - Raio-X Histórico"):
                prices, dividends = get_history(ticker)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if prices is not None and not prices.empty:
                        st.plotly_chart(plot_chart(prices, 'Preço (1 Ano)', 'R$'), use_container_width=True)
                    else:
                        st.warning("Não foi possível buscar o histórico de preços.")
                        
                with col2:
                    if dividends is not None and not dividends.empty:
                        # O erro 'KeyError' foi resolvido aqui, ao passar a Series diretamente.
                        st.plotly_chart(plot_chart(dividends, 'Dividendos (1 Ano)', 'R$'), use_container_width=True)
                    else:
                        st.info("Sem histórico de dividendos no período.")
else:
    # Mensagem de erro clara se o CSV não for encontrado
    st.error("ERRO CRÍTICO: Arquivo `fiis_data.csv` não encontrado. Por favor, siga estes passos:\n\n1. No seu computador, abra o terminal na pasta do projeto.\n2. Execute o comando: `python update_data.py`.\n3. Após a conclusão, envie o arquivo `fiis_data.csv` gerado para o GitHub junto com os outros arquivos do projeto.")

st.markdown("<div style='text-align: center; margin-top: 30px;'><p>FII Compass | Arquitetura Estável</p></div>", unsafe_allow_html=True)
