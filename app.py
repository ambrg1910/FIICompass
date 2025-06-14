# app.py (versão 6.0 - Painel Dinâmico)

import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(page_title="FII Compass Pro", page_icon="🧭", layout="wide")

# -----------------------------------------------------------------------------
# BASE DE DADOS E FUNÇÕES
# -----------------------------------------------------------------------------

# Nossa "base de dados" inicial. Facilmente expansível no futuro.
LISTA_FIIS = [
    'BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11', 
    'HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11', 
    'XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11'
]
# Adicionamos "Tipos" para manter a lógica de pontuação, mesmo que simplificada
# Idealmente, isso viria de uma base de dados mais completa no futuro
FII_TYPES = {
    'BTLG11': 'Tijolo', 'HGLG11': 'Tijolo', 'XPML11': 'Tijolo', 'VISC11': 'Tijolo',
    'HGRU11': 'Tijolo', 'VILG11': 'Tijolo', 'XPLG11': 'Tijolo', 'HGRE11': 'Tijolo', 'LVBI11': 'Tijolo',
    'MXRF11': 'Papel', 'VGIR11': 'Papel', 'KNCR11': 'Papel', 'KNSC11': 'Papel',
    'IRDM11': 'Papel', 'CPTS11': 'Papel', 'RBRR11': 'Papel', 'MCCI11': 'Papel',
    'RECR11': 'Papel', 'HGCR11': 'Papel', 'DEVA11': 'Papel',
    'BCFF11': 'Fundo de Fundos' # Exemplo de outro tipo
}


@st.cache_data(ttl=900)
def get_fii_data_yfinance(ticker):
    try:
        fii = yf.Ticker(f"{ticker}.SA")
        info = fii.info
        
        data = {
            'Ticker': ticker,
            'Tipo': FII_TYPES.get(ticker, 'Outro'),
            'Preço Atual': info.get('regularMarketPrice', info.get('previousClose', 0.0)),
            'DY (12M)': info.get('trailingAnnualDividendYield', 0.0) * 100 if info.get('trailingAnnualDividendYield') else 0.0,
            'Liquidez Diária': info.get('averageVolume', 0),
        }
        return data
    except Exception as e:
        return None

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
        return 10.5

def calculate_scores_api(fii_info, selic):
    dy = fii_info.get('DY (12M)', 0)
    score_dy = 0
    # Pontuação simples baseada no DY vs SELIC
    if dy > selic + 2.0: score_dy = 5
    elif dy > selic: score_dy = 4
    elif dy > selic - 2.0: score_dy = 3
    elif dy > selic - 4.0: score_dy = 2
    else: score_dy = 1
    
    fii_info['Score Final'] = score_dy
    return fii_info

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO (A grande mudança!)
# -----------------------------------------------------------------------------
st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")

# --- Seleção Dinâmica pelo Usuário ---
st.markdown("### 1. Selecione os FIIs para Análise")
fiis_selecionados = st.multiselect(
    'Escolha 2 ou mais FIIs da lista para comparar:',
    options=sorted(LISTA_FIIS),
    default=['BTLG11', 'MXRF11', 'XPML11'] # Uma seleção padrão para facilitar
)

if st.button('Analisar FIIs Selecionados', type="primary", use_container_width=True):
    if len(fiis_selecionados) < 2:
        st.warning("Por favor, selecione pelo menos 2 FIIs para uma análise comparativa.")
    else:
        with st.spinner(f"Analisando {len(fiis_selecionados)} FIIs... Por favor, aguarde."):
            selic_rate = get_selic_rate_from_bcb()
            st.sidebar.metric(label="Taxa SELIC (Referência)", value=f"{selic_rate:.2f}%")
            
            lista_final = []
            for ticker in fiis_selecionados:
                dados = get_fii_data_yfinance(ticker)
                if dados:
                    lista_final.append(calculate_scores_api(dados, selic_rate))
            
            if lista_final:
                st.markdown("### 2. Ranking de Atratividade")
                df = pd.DataFrame(lista_final).sort_values(by='Score Final', ascending=False).reset_index(drop=True)
                df['Recomendação'] = ' '
                if not df.empty and df.loc[0, 'Score Final'] >= 4:
                    df.loc[0, 'Recomendação'] = '🏆 Destaque do Mês'
                
                cols_to_display = ['Ticker', 'Tipo', 'Preço Atual', 'DY (12M)', 'Liquidez Diária', 'Score Final', 'Recomendação']
                st.dataframe(
                    df[cols_to_display].style.format({
                        'Preço Atual': 'R$ {:.2f}', 'DY (12M)': '{:.2f}%', 'Liquidez Diária': '{:,.0f}'
                    }).apply(lambda s: ['background-color: #2E8B57; color: white' if v == '🏆 Destaque do Mês' else '' for v in s], subset=['Recomendação']),
                    use_container_width=True, hide_index=True)
            else:
                st.error("Não foi possível obter dados para os FIIs selecionados. A API pode estar indisponível.")

st.sidebar.header("Condições de Mercado")
with st.sidebar.expander("Glossário de Métricas", expanded=True):
    st.markdown("""
    - **DY (12M):** Dividend Yield anual. Retorno dos dividendos em relação ao preço.
    - **Liq. Diária:** Volume médio de negociação. Maior = mais fácil de negociar.
    - **Score:** Nossa nota de atratividade baseada no rendimento em comparação com a SELIC.
    """)
st.markdown("---")
st.caption("FII Compass | Versão 6.0 - Painel Dinâmico")
