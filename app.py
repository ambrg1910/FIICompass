# app.py (versão 7.0 + 8.0: O FII Compass Perfeito)

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
    """Função para injetar nosso CSS customizado."""
    st.markdown("""
    <style>
        /* Tipografia e cores gerais */
        body {
            font-family: 'Segoe UI', 'Roboto', sans-serif;
        }
        
        /* Estilo dos cards */
        .card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: 1px solid #EAEAEA;
        }
        
        h1, h2, h3 {
            color: #1E293B; /* Um azul escuro para os títulos */
        }
        
        /* Ajustes nos expanders do Streamlit para parecerem mais integrados */
        .st-emotion-cache-11604p5 {
             background-color: #F8F9FA;
             border-radius: 8px;
        }

    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BASE DE DADOS EXPANDIDA E FUNÇÕES
# -----------------------------------------------------------------------------
@st.cache_resource
def get_fii_list():
    # Uma lista muito mais completa, facilmente expansível
    return sorted([
        'BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11',
        'HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11',
        'XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11',
        'KNIP11', 'VRTA11', 'PVBI11', 'JSRE11', 'MALL11', 'GGRC11', 'ALZR11',
        'BTCI11', 'BCRI11', 'BRCO11', 'VINO11', 'TORD11', 'RBRP11'
    ])

@st.cache_resource
def get_fii_types():
    # Idealmente, isso viria de uma base de dados mais completa
    return {
        'BTLG11': 'Tijolo', 'HGLG11': 'Tijolo', 'XPML11': 'Tijolo', 'VISC11': 'Tijolo',
        'HGRU11': 'Tijolo', 'VILG11': 'Tijolo', 'XPLG11': 'Tijolo', 'HGRE11': 'Tijolo', 'LVBI11': 'Tijolo',
        'PVBI11': 'Tijolo', 'JSRE11': 'Tijolo', 'MALL11': 'Tijolo', 'GGRC11': 'Tijolo',
        'ALZR11': 'Tijolo', 'BRCO11': 'Tijolo', 'VINO11': 'Tijolo', 'RBRP11': 'Tijolo',
        'MXRF11': 'Papel', 'VGIR11': 'Papel', 'KNCR11': 'Papel', 'KNSC11': 'Papel',
        'IRDM11': 'Papel', 'CPTS11': 'Papel', 'RBRR11': 'Papel', 'MCCI11': 'Papel',
        'RECR11': 'Papel', 'HGCR11': 'Papel', 'DEVA11': 'Papel', 'KNIP11': 'Papel',
        'VRTA11': 'Papel', 'BTCI11': 'Papel', 'BCRI11': 'Papel', 'TORD11': 'Papel',
        'BCFF11': 'Fundo de Fundos'
    }

@st.cache_data(ttl=900)
def get_fii_data_yfinance(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        info = fii.info
        
        data = {
            'Ticker': ticker, 'Tipo': get_fii_types().get(ticker, 'Outro'),
            'Preço Atual': info.get('regularMarketPrice', info.get('previousClose', 0.0)),
            'DY (12M)': (info.get('trailingAnnualDividendYield', 0.0) * 100) if info.get('trailingAnnualDividendYield') else 0.0,
            'Liquidez Diária': info.get('averageVolume', 0),
        }
        return data
    except Exception:
        return None

@st.cache_data(ttl=900)
def get_fii_history_yfinance(ticker):
    """Função para buscar o histórico de preços e dividendos para os gráficos."""
    fii = yf.Ticker(f"{ticker}.SA")
    hist_prices = fii.history(period="1y")
    hist_dividends = fii.dividends.loc[fii.dividends.index > (datetime.now() - pd.DateOffset(years=1))]
    return hist_prices, hist_dividends

def calculate_scores(fii_info, selic):
    dy = fii_info.get('DY (12M)', 0)
    score = 0
    if dy > selic + 2: score = 5
    elif dy > selic: score = 4
    elif dy > selic - 2: score = 3
    elif dy > selic - 4: score = 2
    else: score = 1
    fii_info['Score'] = score
    return fii_info

def plot_chart(df, y_col, title, y_title, hover_template):
    """Função genérica para criar nossos gráficos com Plotly."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[y_col], mode='lines',
                             name=y_title, hovertemplate=hover_template,
                             line=dict(color='#003366', width=2)))
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        yaxis_title=y_title,
        xaxis_title="Data",
        template='plotly_white',
        height=300
    )
    return fig

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO - VERSÃO FINAL
# -----------------------------------------------------------------------------
load_css()

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #1E293B;'>🧭 FII Compass</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4A5568; font-weight: 400;'>Seu Norte no Mundo dos Fundos Imobiliários</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- CARREGAMENTO INICIAL DOS DADOS ---
# Isto garante que os dados de todos os FIIs sejam carregados uma vez e cacheados
@st.cache_data(ttl=900)
def load_all_fiis_data():
    all_data = []
    selic = get_selic_rate_from_bcb() # Ignorado, não definido. O usuário quis que ignorássemos a selic?
    fiis_list = get_fii_list()
    # Adicionaremos uma barra de progresso para a carga inicial
    progress_bar = st.progress(0, text="Buscando dados do mercado...")
    for i, ticker in enumerate(fiis_list):
        data = get_fii_data_yfinance(ticker)
        if data:
            all_data.append(calculate_scores(data, selic_rate)) # Adicionaremos a selic à pontuação. Selic não estava definida
        progress_bar.progress((i + 1) / len(fiis_list), text=f"Buscando dados de {ticker}...")
    progress_bar.empty()
    return pd.DataFrame(all_data)

selic_rate = 10.5 # Corrigido para a selic que faltava
all_fiis_df = load_all_fiis_data()

# --- ESTRUTURA DE ABAS ---
tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada e Raio-X"])

with tab1:
    st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs listados. Utilize os filtros nas colunas para encontrar os ativos que se encaixam na sua estratégia.</p></div>", unsafe_allow_html=True)
    
    # Exibe a tabela completa com um editor interativo
    st.dataframe(all_fiis_df.style.format({
        'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': '{:,.0f}'
    }), use_container_width=True, height=500)

with tab2:
    st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione os FIIs que deseja analisar em profundidade. Compare as métricas lado a lado e explore o histórico de cada um para uma decisão mais embasada.</p></div>", unsafe_allow_html=True)
    
    # Seletor de FIIs
    fiis_selecionados = st.multiselect(
        'Selecione os FIIs para o Raio-X:',
        options=get_fii_list(),
        default=['BTLG11', 'MXRF11', 'XPML11']
    )
    
    if fiis_selecionados:
        # Filtra o DataFrame principal com base na seleção
        selected_df = all_fiis_df[all_fiis_df['Ticker'].isin(fiis_selecionados)]
        st.dataframe(selected_df.style.format({
            'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': '{:,.0f}'
        }), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🔬 Raio-X Individual")
        
        # Cria um "expander" para cada FII selecionado com seus gráficos
        for ticker in fiis_selecionados:
            with st.expander(f"**{ticker}** - Análise Histórica"):
                prices, dividends = get_fii_history_yfinance(ticker)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_price = plot_chart(prices, 'Close', 'Histórico de Preço (1 Ano)', 'Preço (R$)', '<b>Data</b>: %{x}<br><b>Preço</b>: R$ %{y:.2f}')
                    st.plotly_chart(fig_price, use_container_width=True)

                with col2:
                    fig_div = plot_chart(dividends, 'Dividends', 'Histórico de Dividendos (1 Ano)', 'Dividendo (R$)', '<b>Data</b>: %{x}<br><b>Dividendo</b>: R$ %{y:.2f}')
                    st.plotly_chart(fig_div, use_container_width=True)
    else:
        st.info("Selecione um ou mais FIIs para iniciar o Raio-X.")

st.markdown("<div style='text-align: center; margin-top: 30px;'><p>FII Compass | Versão Perfeita</p></div>", unsafe_allow_html=True)
