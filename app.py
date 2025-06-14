# app.py (versão 5.0 - API-Powered com yfinance)

import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf # A nossa nova ferramenta principal!

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FII Compass Pro",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# FUNÇÃO DE BUSCA DE DADOS (USANDO yfinance API)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900)
def get_fii_data_yfinance(ticker):
    """
    Busca os dados de um FII usando a biblioteca yfinance.
    Mais robusto e confiável que web scraping.
    """
    try:
        # Adicionamos '.SA' para indicar que o ticker é da bolsa de São Paulo
        fii = yf.Ticker(f"{ticker}.SA")
        info = fii.info

        # yfinance não tem P/VP ou Nº de Cotistas direto para FIIs.
        # Por isso, vamos focar nas métricas mais confiáveis que a API oferece
        # e adaptar nosso dashboard.
        data = {
            'Preço Atual': info.get('regularMarketPrice', info.get('previousClose', 0.0)),
            'DY (12M)': info.get('trailingAnnualDividendYield', 0.0) * 100 if info.get('trailingAnnualDividendYield') else 0.0,
            'Liquidez Diária': info.get('averageVolume', 0),
            'Patrimônio Líquido': info.get('totalAssets', 0)
        }
        
        # P/VP precisa de um cálculo manual e de dados que a API nem sempre fornece de forma limpa para FIIs.
        # Vamos omiti-lo por enquanto para garantir estabilidade máxima.
        # Nossa pontuação será baseada apenas no DY por enquanto.
        return data

    except Exception as e:
        st.warning(f"Não foi possível buscar dados para {ticker} via API yfinance. Erro: {e}")
        return None

# Função da SELIC (sem alterações, já é robusta)
@st.cache_data(ttl=3600)
def get_selic_rate_from_bcb():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        selic_diaria = float(response.json()[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100
    except:
        return 10.5 # Fallback

# -----------------------------------------------------------------------------
# LÓGICA DE PONTUAÇÃO (SIMPLIFICADA E ADAPTADA PARA OS DADOS DA API)
# -----------------------------------------------------------------------------
def calculate_scores_api(fii_info, selic):
    """
    Lógica de pontuação adaptada para os dados disponíveis na API.
    Focaremos no DY como principal indicador de atratividade por enquanto.
    """
    dy = fii_info.get('DY (12M)', 0)
    score_dy = 0

    # Usaremos a mesma lógica de antes, mas agora ela é a única fonte de pontos
    if dy > selic + 3.0: score_dy = 5
    elif dy > selic + 1.5: score_dy = 4
    elif dy > selic: score_dy = 3
    elif dy > selic - 2.0: score_dy = 2
    else: score_dy = 1

    fii_info['Score Final'] = score_dy
    return fii_info

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO
# -----------------------------------------------------------------------------
st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")

fiis_a_analisar = [{'Ticker': 'BTLG11', 'Tipo': 'Tijolo'},{'Ticker': 'MXRF11', 'Tipo': 'Papel'},{'Ticker': 'VGIR11', 'Tipo': 'Papel'}]
selic_rate = get_selic_rate_from_bcb()

st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC (Anualizada)", value=f"{selic_rate:.2f}%")
st.sidebar.caption("Fonte: Banco Central do Brasil.")
st.sidebar.markdown("---")
with st.sidebar.expander("Glossário de Métricas"):
    st.markdown("""
    - **DY (12M):** Dividend Yield anual.
    - **Liq. Diária:** Volume médio de negociação.
    - **Patrim. Líq.:** O valor total dos ativos do fundo.
    """)

if st.button('Analisar Meus FIIs', type="primary", use_container_width=True):
    with st.spinner('Conectando à API do mercado...'):
        lista_final = []
        for fii in fiis_a_analisar:
            # Usando a nova função baseada em API
            dados = get_fii_data_yfinance(fii['Ticker'])
            if dados:
                fii_completo = {**fii, **dados}
                fii_analisado = calculate_scores_api(fii_completo, selic_rate)
                lista_final.append(fii_analisado)
        
        if lista_final:
            df = pd.DataFrame(lista_final).sort_values(by='Score Final', ascending=False).reset_index(drop=True)
            df['Recomendação'] = ' '
            if not df.empty and df.loc[0, 'Score Final'] > 2:
                df.loc[0, 'Recomendação'] = '🏆 Aporte do Mês'
            
            # Adaptamos as colunas para o que a API nos oferece de forma confiável
            cols_to_display = ['Ticker', 'Tipo', 'Preço Atual', 'DY (12M)', 'Liquidez Diária', 'Patrimônio Líquido', 'Score Final', 'Recomendação']
            df_display = df[cols_to_display]
            
            st.subheader("Ranking de Atratividade para Aporte")
            st.dataframe(
                df_display.style.format({
                    'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': '{:,.0f}', 'Patrimônio Líquido': 'R$ {:,.0f}'
                }).apply(lambda s: ['background-color: #2E8B57; color: white' if v == '🏆 Aporte do Mês' else '' for v in s], subset=['Recomendação']),
                use_container_width=True, hide_index=True)
        else:
            st.error("Não foi possível obter dados para nenhum FII via API. Verifique os tickers e tente novamente.")

st.markdown("---")
st.caption("FII Compass | Versão 5.0 - API-Powered")
