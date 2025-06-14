# app.py (versão 4.2 - Correção Definitiva do KeyError)

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
    page_title="FII Compass Pro",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# FUNÇÃO DE BUSCA DE DADOS (VERSÃO BLINDADA / "PARANOICA")
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900)
def get_fii_data_from_fundamentus(ticker):
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Se a página não carregar, isso vai lançar um erro.
        soup = BeautifulSoup(response.text, 'html.parser')

        # PASSO 1: Criar o dicionário 'esqueleto'. Ele SEMPRE terá todas as chaves.
        data = {
            'Preço Atual': 0.0,
            'P/VP': 0.0,
            'DY (12M)': 0.0,
            'Liquidez Diária': 0.0,
            'Nº de Cotistas': 0,
            'Últ. Rend. (R$)': 0.0
        }

        # Helper function para encontrar o valor de forma segura
        def find_value(soup_obj, label_text):
            element = soup_obj.find('td', class_='label', text=re.compile(label_text))
            if element and element.find_next_sibling('td'):
                return element.find_next_sibling('td').text.strip()
            return None
        
        # PASSO 2: Tentar preencher cada campo, um por um, de forma segura.
        try:
            price_str = find_value(soup, 'Cotação')
            if price_str: data['Preço Atual'] = float(price_str.replace('.', '').replace(',', '.'))
        except (ValueError, TypeError): pass # Se falhar, o valor continua 0.0
        
        try:
            pvp_str = find_value(soup, 'P/VP')
            if pvp_str: data['P/VP'] = float(pvp_str.replace(',', '.'))
        except (ValueError, TypeError): pass

        try:
            dy_str = find_value(soup, 'Div. Yield')
            if dy_str: data['DY (12M)'] = float(dy_str.replace('%', '').replace(',', '.'))
        except (ValueError, TypeError): pass

        try:
            liq_str = find_value(soup, 'Liq. 2 meses')
            if liq_str: data['Liquidez Diária'] = float(liq_str.replace('.', '').replace(',', '.'))
        except (ValueError, TypeError): pass
            
        try:
            cotistas_str = find_value(soup, 'Nro. Cotistas')
            if cotistas_str: data['Nº de Cotistas'] = int(cotistas_str)
        except (ValueError, TypeError): pass

        try:
            ult_rend_str = find_value(soup, 'Último Rend.')
            if ult_rend_str: data['Últ. Rend. (R$)'] = float(ult_rend_str.replace('R$', '').strip().replace(',', '.'))
        except (ValueError, TypeError): pass

        return data

    except requests.exceptions.RequestException as e:
        st.warning(f"Não foi possível conectar ao Fundamentus para buscar dados de {ticker}. Erro: {e}")
        return None # Se a página inteira falhar, retornamos None e o app tratará disso.

# As demais funções não precisam de alteração
@st.cache_data(ttl=3600)
def get_selic_rate_from_bcb():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()
        selic_diaria = float(data[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100
    except Exception as e:
        st.warning(f"Não foi possível buscar a SELIC. Usando valor padrão. Erro: {e}")
        return 10.5

def calculate_scores(fii_info, selic):
    p_vp = fii_info.get('P/VP', 0)
    score_pvp, score_dy, score_final = 0, 0, 0
    if fii_info['Tipo'] == 'Tijolo':
        if 0 < p_vp < 0.98: score_pvp = 3
        elif p_vp < 1.02: score_pvp = 2
        elif p_vp < 1.05: score_pvp = 1
    elif fii_info['Tipo'] == 'Papel':
        if 0 < p_vp < 1.01: score_pvp = 3
        elif p_vp < 1.04: score_pvp = 2
        elif p_vp < 1.06: score_pvp = 1
    
    dy = fii_info.get('DY (12M)', 0)
    if fii_info['Tipo'] == 'Tijolo':
        if dy > selic + 2.0: score_dy = 3
        elif dy > selic: score_dy = 2
        elif dy >= selic - 2.0: score_dy = 1
    elif fii_info['Tipo'] == 'Papel':
        if dy > selic + 3.0: score_dy = 3
        elif dy > selic + 1.5: score_dy = 2
        elif dy > selic: score_dy = 1
    if p_vp > 0: # Só pontua se o P/VP for válido
        if fii_info['Tipo'] == 'Tijolo': score_final = (score_pvp * 2) + (score_dy * 1)
        elif fii_info['Tipo'] == 'Papel': score_final = (score_pvp * 1) + (score_dy * 2)
    fii_info['Score Final'] = score_final
    return fii_info

st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")
fiis_a_analisar = [{'Ticker': 'BTLG11', 'Tipo': 'Tijolo'}, {'Ticker': 'MXRF11', 'Tipo': 'Papel'}, {'Ticker': 'VGIR11', 'Tipo': 'Papel'}]
selic_rate = get_selic_rate_from_bcb()
st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC (Anualizada)", value=f"{selic_rate:.2f}%")
st.sidebar.caption("Fonte: Banco Central do Brasil.")
st.sidebar.markdown("---")
with st.sidebar.expander("Glossário de Métricas"):
    st.markdown("""
- **P/VP:** Preço / Valor Patrimonial. Abaixo de 1 pode indicar "desconto".
- **DY (12M):** Dividend Yield anualizado.
- **Liq. Diária:** Liquidez média diária. Maior = mais fácil de negociar.
- **Nº Cotistas:** Total de investidores no fundo.
- **Últ. Rend.:** Rendimento pago no último mês por cota.
""")
if st.button('Analisar Meus FIIs', type="primary", use_container_width=True):
    with st.spinner('Analisando o mercado para você...'):
        lista_final = []
        for fii in fiis_a_analisar:
            dados = get_fii_data_from_fundamentus(fii['Ticker'])
            if dados:
                lista_final.append(calculate_scores({**fii, **dados}, selic_rate))
        
        if lista_final:
            df = pd.DataFrame(lista_final).sort_values(by='Score Final', ascending=False).reset_index(drop=True)
            df['Recomendação'] = ''
            if not df.empty:
                df.loc[0, 'Recomendação'] = '🏆 Aporte do Mês'
                if df.loc[0, 'Score Final'] < 4:
                    df.loc[0, 'Recomendação'] = '⚠️ Nenhuma Oportunidade Clara'
            
            cols_to_display = ['Ticker', 'Tipo', 'Preço Atual', 'P/VP', 'DY (12M)', 'Liq. Diária', 'Nº de Cotistas', 'Últ. Rend. (R$)', 'Score Final', 'Recomendação']
            df_display = df[cols_to_display]
            
            st.subheader("Ranking de Atratividade para Aporte")
            st.dataframe(df_display.style.format({
                'Preço Atual': 'R$ {:.2f}','P/VP': '{:.2f}','DY (12M)': '{:.2f}%','Liq. Diária': 'R$ {:,.0f}','Nº de Cotistas': '{:,}','Últ. Rend. (R$)': 'R$ {:.2f}'
            }).apply(lambda s: ['background-color: #2E8B57; color: white' if v == '🏆 Aporte do Mês' else '' for v in s], subset=['Recomendação']),use_container_width=True,hide_index=True)
        else:
            st.error("Não foi possível obter dados para nenhum dos FIIs. A fonte de dados pode estar indisponível.")
st.markdown("---")
st.caption("FII Compass | Versão 4.2 - Robusta")
