# app.py (versão 2.0 - mais robusta)

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FII Compass",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# FUNÇÕES DE BUSCA DE DADOS (O Robô que coleta as informações)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=900)
def get_fii_data(ticker):
    """Busca os dados de um FII específico no site Status Invest."""
    url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.warning(f"Não foi possível buscar dados para {ticker}. Status: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Preço Atual
        price = float(soup.find('strong', class_='value').text.replace(',', '.'))
        # VP por Cota
        vp_element = soup.find('h4', string='Valor patrimonial p/ cota').find_next('strong')
        vp = float(vp_element.text.replace(',', '.'))
        # DY (12M)
        dy_element = soup.find('h4', string='Dividend Yield').find_next('strong')
        dy = float(dy_element.text.replace(',', '.'))
        
        return {'Preço Atual': price, 'VP por Cota': vp, 'DY (12M)': dy}

    except Exception as e:
        st.error(f"Erro ao processar dados para {ticker}. O site pode ter alterado seu layout. Detalhe: {e}")
        return None

# NOVA FUNÇÃO, MAIS ROBUSTA E OFICIAL
@st.cache_data(ttl=3600) # SELIC muda com menos frequência, cache de 1 hora
def get_selic_rate_from_bcb():
    """Busca a taxa SELIC Over (mais próxima da Meta) direto da API do Banco Central."""
    try:
        # URL da API de Séries Temporais do Banco Central para a SELIC diária (código da série: 11)
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url)
        response.raise_for_status() # Lança erro se a requisição falhar
        data = response.json()
        
        # A API retorna o valor como percentual ao dia. Multiplicamos para ter a taxa anualizada aproximada.
        # A taxa da API (11) é a Selic Over, que é muito próxima da Meta. A conversão é uma convenção comum.
        selic_diaria = float(data[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100

    except Exception as e:
        st.warning(f"Não foi possível buscar a taxa SELIC na API do Banco Central. Usando valor padrão de 10.5%. Erro: {e}")
        return 10.5 # Valor de fallback

# -----------------------------------------------------------------------------
# O CÉREBRO: LÓGICA DE PONTUAÇÃO (Nossa Estratégia em Código)
# -----------------------------------------------------------------------------
def calculate_scores(fii_info, selic):
    # O restante da lógica permanece exatamente igual...
    if fii_info['VP por Cota'] > 0:
        p_vp = fii_info['Preço Atual'] / fii_info['VP por Cota']
    else:
        p_vp = 0
    fii_info['P/VP'] = p_vp
    
    score_pvp, score_dy, score_final = 0, 0, 0

    if fii_info['Tipo'] == 'Tijolo':
        if p_vp < 0.98: score_pvp = 3
        elif p_vp < 1.02: score_pvp = 2
        elif p_vp < 1.05: score_pvp = 1
    elif fii_info['Tipo'] == 'Papel':
        if p_vp < 1.01: score_pvp = 3
        elif p_vp < 1.04: score_pvp = 2
        elif p_vp < 1.06: score_pvp = 1
    
    dy = fii_info['DY (12M)']
    if fii_info['Tipo'] == 'Tijolo':
        if dy > selic + 2.0: score_dy = 3
        elif dy > selic: score_dy = 2
        elif dy >= selic - 2.0: score_dy = 1
    elif fii_info['Tipo'] == 'Papel':
        if dy > selic + 3.0: score_dy = 3
        elif dy > selic + 1.5: score_dy = 2
        elif dy > selic: score_dy = 1

    if fii_info['Tipo'] == 'Tijolo': score_final = (score_pvp * 2) + (score_dy * 1)
    elif fii_info['Tipo'] == 'Papel': score_final = (score_pvp * 1) + (score_dy * 2)

    fii_info['Score Final'] = score_final
    return fii_info

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO (O que aparece na tela)
# -----------------------------------------------------------------------------
st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")
st.markdown(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

fiis_a_analisar = [
    {'Ticker': 'BTLG11', 'Tipo': 'Tijolo'},
    {'Ticker': 'MXRF11', 'Tipo': 'Papel'},
    {'Ticker': 'VGIR11', 'Tipo': 'Papel'},
]

# USAMOS A NOVA FUNÇÃO AQUI
selic_rate = get_selic_rate_from_bcb()

st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC (Anualizada)", value=f"{selic_rate:.2f}%")
st.sidebar.caption("Taxa Selic Over, fonte: Banco Central do Brasil. Usada como referência para o retorno dos FIIs.")

if st.button('Analisar Meus FIIs', type="primary"):
    with st.spinner('Buscando dados e calculando scores... Por favor, aguarde.'):
        lista_final = [fii_analisado for fii in fiis_a_analisar if (dados := get_fii_data(fii['Ticker'])) and (fii_analisado := calculate_scores({**fii, **dados}, selic_rate))]
        
        if lista_final:
            df = pd.DataFrame(lista_final).sort_values(by='Score Final', ascending=False).reset_index(drop=True)
            df['Recomendação'] = ''
            if not df.empty:
                df.loc[0, 'Recomendação'] = '🏆 Aporte do Mês'
                if df.loc[0, 'Score Final'] < 4:
                    df.loc[0, 'Recomendação'] = '⚠️ Nenhuma Oportunidade Clara'
            
            df_display = df[['Ticker', 'Tipo', 'Preço Atual', 'P/VP', 'DY (12M)', 'Score Final', 'Recomendação']]
            st.subheader("Ranking de Atratividade para Aporte")
            
            st.dataframe(df_display.style.format({'Preço Atual': 'R$ {:.2f}', 'P/VP': '{:.2f}', 'DY (12M)': '{:.2f}%'}).apply(lambda s: ['background-color: #2E8B57; color: white' if v == '🏆 Aporte do Mês' else '' for v in s], subset=['Recomendação']), use_container_width=True, hide_index=True)
        else:
            st.error("Não foi possível obter dados para nenhum dos FIIs. Tente novamente mais tarde.")

st.markdown("---")
st.caption("Desenvolvido com base na estratégia do Expert em Investimentos. Versão 2.0")
