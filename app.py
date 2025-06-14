# app.py (versão 3.0 - Fonte de dados alternativa)

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FII Compass",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# FUNÇÕES DE BUSCA DE DADOS (O Robô agora conversa com o Fundamentus)
# -----------------------------------------------------------------------------

# NOVA FUNÇÃO, AGORA BUSCANDO NO FUNDAMENTUS
@st.cache_data(ttl=900)
def get_fii_data_from_fundamentus(ticker):
    """
    Busca os dados de um FII específico no site Fundamentus.
    """
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontra todos os dados na tabela
        # A estrutura do site é uma tabela, buscamos o texto âncora e pegamos o próximo elemento
        def get_value_by_label(label):
            element = soup.find(text=re.compile(label))
            if element:
                return element.find_next('span', class_='txt').text.strip()
            return '0'
        
        # O Fundamentus chama o Valor Patrimonial de VPA (Valor Patrimonial por Ação)
        price = float(get_value_by_label('Cotação').replace(',', '.'))
        vp = float(get_value_by_label('VPA').replace(',', '.')) 
        p_vp = float(get_value_by_label('P/VP').replace(',', '.'))
        
        # O DY precisa de um tratamento especial para remover o '%'
        dy_str = get_value_by_label('Div. Yield')
        dy = float(dy_str.replace('%', '').replace(',', '.'))
        
        return {'Preço Atual': price, 'VP por Cota': vp, 'P/VP': p_vp, 'DY (12M)': dy}

    except Exception as e:
        st.warning(f"Não foi possível buscar dados para {ticker} no Fundamentus. Status: 403. Detalhe: {e}")
        return None


# Função para a SELIC, que já está funcionando bem
@st.cache_data(ttl=3600)
def get_selic_rate_from_bcb():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        selic_diaria = float(data[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100
    except Exception as e:
        st.warning(f"Não foi possível buscar a taxa SELIC na API do Banco Central. Usando valor padrão de 10.5%. Erro: {e}")
        return 10.5

# -----------------------------------------------------------------------------
# O CÉREBRO: LÓGICA DE PONTUAÇÃO (Levemente ajustado)
# -----------------------------------------------------------------------------

def calculate_scores(fii_info, selic):
    """
    Calcula os scores. Agora recebe P/VP diretamente.
    """
    p_vp = fii_info.get('P/VP', 0) # Pega o P/VP que já veio do Fundamentus

    score_pvp, score_dy, score_final = 0, 0, 0
    
    # Lógica de pontuação de P/VP (sem alterações)
    if fii_info['Tipo'] == 'Tijolo':
        if p_vp < 0.98: score_pvp = 3
        elif p_vp < 1.02: score_pvp = 2
        elif p_vp < 1.05: score_pvp = 1
    elif fii_info['Tipo'] == 'Papel':
        if p_vp < 1.01: score_pvp = 3
        elif p_vp < 1.04: score_pvp = 2
        elif p_vp < 1.06: score_pvp = 1
    
    # Lógica de pontuação de DY (sem alterações)
    dy = fii_info.get('DY (12M)', 0)
    if fii_info['Tipo'] == 'Tijolo':
        if dy > selic + 2.0: score_dy = 3
        elif dy > selic: score_dy = 2
        elif dy >= selic - 2.0: score_dy = 1
    elif fii_info['Tipo'] == 'Papel':
        if dy > selic + 3.0: score_dy = 3
        elif dy > selic + 1.5: score_dy = 2
        elif dy > selic: score_dy = 1

    # Lógica de pesos (sem alterações)
    if fii_info['Tipo'] == 'Tijolo': score_final = (score_pvp * 2) + (score_dy * 1)
    elif fii_info['Tipo'] == 'Papel': score_final = (score_pvp * 1) + (score_dy * 2)

    fii_info['Score Final'] = score_final
    return fii_info

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO
# -----------------------------------------------------------------------------

st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")
st.markdown(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

fiis_a_analisar = [
    {'Ticker': 'BTLG11', 'Tipo': 'Tijolo'},
    {'Ticker': 'MXRF11', 'Tipo': 'Papel'},
    {'Ticker': 'VGIR11', 'Tipo': 'Papel'},
]

selic_rate = get_selic_rate_from_bcb()

st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC (Anualizada)", value=f"{selic_rate:.2f}%")
st.sidebar.caption("Taxa Selic Over, fonte: Banco Central do Brasil. Usada como referência para o retorno dos FIIs.")

if st.button('Analisar Meus FIIs', type="primary"):
    with st.spinner('Buscando dados no Fundamentus e calculando scores...'):
        
        lista_final = []
        for fii in fiis_a_analisar:
            # CHAMAMOS A NOVA FUNÇÃO AQUI
            dados = get_fii_data_from_fundamentus(fii['Ticker'])
            if dados:
                fii_completo = {**fii, **dados}
                fii_analisado = calculate_scores(fii_completo, selic_rate)
                lista_final.append(fii_analisado)
        
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
            st.error("Não foi possível obter dados para nenhum dos FIIs. Verifique se os tickers estão corretos e tente novamente.")

st.markdown("---")
st.caption("Desenvolvido com base na estratégia do Expert em Investimentos. Versão 3.0 - Anti-Bloqueio")
