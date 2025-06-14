# app.py (versão 10.0 - A Arquitetura Final: Paciência e Robustez)

import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import time # Importamos a biblioteca para controlar o tempo

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
# BASE DE DADOS E FUNÇÕES
# -----------------------------------------------------------------------------
@st.cache_resource
def get_fii_list():
    return sorted(['BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11','HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11','XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11','KNIP11', 'VRTA11', 'PVBI11', 'JSRE11', 'MALL11', 'GGRC11', 'ALZR11','BTCI11', 'BCRI11', 'BRCO11', 'VINO11', 'TORD11', 'RBRP11'])

@st.cache_resource
def get_fii_types():
    return { 'BTLG11': 'Tijolo', 'HGLG11': 'Tijolo', 'XPML11': 'Tijolo', 'VISC11': 'Tijolo','HGRU11': 'Tijolo', 'VILG11': 'Tijolo', 'XPLG11': 'Tijolo', 'HGRE11': 'Tijolo', 'LVBI11': 'Tijolo','PVBI11': 'Tijolo', 'JSRE11': 'Tijolo', 'MALL11': 'Tijolo', 'GGRC11': 'Tijolo','ALZR11': 'Tijolo', 'BRCO11': 'Tijolo', 'VINO11': 'Tijolo', 'RBRP11': 'Tijolo','MXRF11': 'Papel', 'VGIR11': 'Papel', 'KNCR11': 'Papel', 'KNSC11': 'Papel','IRDM11': 'Papel', 'CPTS11': 'Papel', 'RBRR11': 'Papel', 'MCCI11': 'Papel','RECR11': 'Papel', 'HGCR11': 'Papel', 'DEVA11': 'Papel', 'KNIP11': 'Papel','VRTA11': 'Papel', 'BTCI11': 'Papel', 'BCRI11': 'Papel', 'TORD11': 'Papel','BCFF11': 'Fundo de Fundos'}

@st.cache_data(ttl=900)
def get_fii_data_yfinance(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        info = fii.info
        dividends_last_12m = fii.dividends.loc[fii.dividends.index > (datetime.now() - pd.DateOffset(years=1))].sum()
        price = info.get('regularMarketPrice', 0.0)
        dy_12m = (dividends_last_12m / price * 100) if price > 0 else 0.0
        return {'Ticker': ticker, 'Tipo': get_fii_types().get(ticker, 'Outro'),'Preço Atual': price, 'DY (12M)': dy_12m,'Liquidez Diária': info.get('averageVolume', 0)}
    except Exception: return None

@st.cache_data(ttl=900)
def get_fii_history_yfinance(ticker):
    fii = yf.Ticker(f"{ticker}.SA")
    hist_prices = fii.history(period="1y")
    one_year_ago = datetime.now() - pd.DateOffset(years=1)
    if fii.dividends.index.tz is not None: one_year_ago = pd.to_datetime(one_year_ago).tz_localize(fii.dividends.index.tz)
    hist_dividends = fii.dividends.loc[fii.dividends.index > one_year_ago]
    return hist_prices, hist_dividends

@st.cache_data(ttl=86400)
def get_selic_rate_from_bcb():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        selic_diaria = float(response.json()[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100
    except: return 10.5

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
    fig = go.Figure(go.Scatter(x=df.index, y=df[y_col], mode='lines', name=y_title, hovertemplate=hover_template, line=dict(color='#003366', width=2)))
    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=18)), yaxis_title=y_title, xaxis_title="Data", template='plotly_white', height=300, margin=dict(t=50, b=10, l=10, r=10))
    return fig

# --- FUNÇÃO DE CARGA FINAL, LENTA E SEGURA ---
@st.cache_data(ttl=900)
def load_all_fiis_data(selic_rate):
    all_data = []
    fiis_list = get_fii_list()
    progress_bar = st.progress(0, text="Iniciando conexão com o mercado...")

    for i, ticker in enumerate(fiis_list):
        # 1. Busca os dados de UM FII de cada vez
        data = get_fii_data_yfinance(ticker)
        if data:
            all_data.append(calculate_scores(data, selic_rate))
        
        # 2. Atualiza a barra de progresso para o usuário
        progress_bar.progress((i + 1) / len(fiis_list), text=f"Analisando {i+1}/{len(fiis_list)}: {ticker}...")
        
        # 3. ### A CHAVE DA VITÓRIA: PAUSA DELIBERADA ###
        # Fazemos uma pequena pausa para não sobrecarregar a API
        time.sleep(0.1)

    progress_bar.empty()
    
    # Garantia de que não criaremos um DataFrame vazio se tudo falhar
    if not all_data:
        return pd.DataFrame()
        
    return pd.DataFrame(all_data)

# --- INÍCIO DA EXECUÇÃO DA INTERFACE ---
load_css()
st.markdown("<h1 style='text-align: center; color: #1E293B;'>🧭 FII Compass</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4A5568; font-weight: 400;'>Seu Norte no Mundo dos Fundos Imobiliários</h3>", unsafe_allow_html=True)
st.markdown("---")

selic_atual = get_selic_rate_from_bcb()
all_fiis_df = load_all_fiis_data(selic_atual)

# --- ESTRUTURA DE ABAS ---
tab1, tab2 = st.tabs(["📊 Visão Geral do Mercado", "🔬 Análise Detalhada e Raio-X"])

with tab1:
    st.markdown("<div class='card'><h3>Panorama Completo do Mercado</h3><p>Explore e compare os principais FIIs listados. Utilize os filtros e a ordenação nas colunas para encontrar os ativos que se encaixam na sua estratégia.</p></div>", unsafe_allow_html=True)
    if not all_fiis_df.empty:
        st.dataframe(all_fiis_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, height=600)
    else:
        st.error("Não foi possível carregar os dados do mercado. A API pode estar com instabilidade. Por favor, tente atualizar a página em alguns minutos.")

# A Lógica da Aba 2 permanece a mesma, pois agora ela recebe um DataFrame confiável
with tab2:
    st.markdown("<div class='card'><h3>Análise Comparativa e Raio-X</h3><p>Selecione os FIIs que deseja analisar em profundidade. Compare as métricas lado a lado e explore o histórico de cada um para uma decisão mais embasada.</p></div>", unsafe_allow_html=True)
    fiis_selecionados = st.multiselect('Selecione os FIIs para o Raio-X:', options=get_fii_list(), default=['BTLG11', 'MXRF11', 'XPML11'])
    if fiis_selecionados:
        if not all_fiis_df.empty:
            selected_df = all_fiis_df[all_fiis_df['Ticker'].isin(fiis_selecionados)]
            if not selected_df.empty:
                st.dataframe(selected_df.style.format({'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': 'R$ {:,.0f}'}), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("### 🔬 Raio-X Individual")
        for ticker in fiis_selecionados:
            with st.expander(f"**{ticker}** - Análise Histórica"):
                try:
                    prices, dividends = get_fii_history_yfinance(ticker)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(plot_chart(prices, 'Close', 'Preço (1 Ano)', 'R$', '<b>Data</b>: %{x}<br><b>Preço</b>: R$ %{y:.2f}'), use_container_width=True)
                    with col2:
                        if not dividends.empty:
                            st.plotly_chart(plot_chart(dividends, 'Dividends', 'Dividendos (1 Ano)', 'R$', '<b>Data</b>: %{x}<br><b>Dividendo</b>: R$ %{y:.2f}'), use_container_width=True)
                        else: st.info("Sem dividendos registrados no último ano.")
                except Exception as e:
                    st.error(f"Não foi possível gerar os gráficos para {ticker}. Erro: {e}")
    else: st.info("Selecione um ou mais FIIs para o Raio-X.")

st.markdown("<div style='text-align: center; margin-top: 30px;'><p>FII Compass | Arquitetura Definitiva</p></div>", unsafe_allow_html=True)
