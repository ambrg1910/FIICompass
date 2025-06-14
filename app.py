# app.py (versão 4.1 - Bugfix KeyError)

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
# FUNÇÃO DE BUSCA DE DADOS (AGORA BLINDADA CONTRA ERROS)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=900)
def get_fii_data_from_fundamentus(ticker):
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Dicionário de dados que VAMOS GARANTIR que seja preenchido
        data = {
            'Preço Atual': 0.0,
            'P/VP': 0.0,
            'DY (12M)': 0.0,
            'Liquidez Diária': 0.0,
            'Nº de Cotistas': 0,
            'Últ. Rend. (R$)': 0.0
        }

        # Helper function robusta para buscar o valor
        def get_value_by_label(soup_obj, label):
            try:
                # Procura uma <td> com a label, depois pega o texto da próxima <td>
                element = soup_obj.find('td', class_='label', text=re.compile(label))
                if element and element.find_next_sibling('td'):
                    value_str = element.find_next_sibling('td').text.strip()
                    # Limpa e converte o valor para float
                    return float(value_str.replace('.', '').replace(',', '.').replace('%', ''))
                return 0.0
            except (ValueError, AttributeError):
                return 0.0

        # Preenchendo o dicionário de forma segura
        data['Preço Atual'] = get_value_by_label(soup, 'Cotação')
        data['P/VP'] = get_value_by_label(soup, 'P/VP')
        data['DY (12M)'] = get_value_by_label(soup, 'Div. Yield')
        data['Liquidez Diária'] = get_value_by_label(soup, 'Liq. 2 meses')
        data['Nº de Cotistas'] = int(get_value_by_label(soup, 'Nro. Cotistas'))
        
        # Último rendimento tem R$ na frente, tratamos separadamente
        try:
            ult_rend_element = soup.find('td', class_='label', text=re.compile('Último Rend.'))
            if ult_rend_element:
                value_str = ult_rend_element.find_next_sibling('td').text.strip().replace('R$','').replace(' ','')
                data['Últ. Rend. (R$)'] = float(value_str.replace(',', '.'))
        except (ValueError, AttributeError):
             data['Últ. Rend. (R$)'] = 0.0

        return data

    except Exception as e:
        st.warning(f"Não foi possível buscar dados para {ticker}. Erro geral: {e}")
        return None # Se a página inteira falhar, retornamos None


# Função da SELIC (sem alterações)
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
    except:
        return 10.5 # Fallback


# Lógica de pontuação e Interface do Usuário permanecem as mesmas
# O CÉREBRO: LÓGICA DE PONTUAÇÃO (Sem alterações na lógica principal)
def calculate_scores(fii_info, selic):
    p_vp = fii_info.get('P/VP', 0)
    score_pvp, score_dy, score_final = 0, 0, 0
    if fii_info['Tipo'] == 'Tijolo':
        if p_vp < 0.98: score_pvp = 3
        elif p_vp < 1.02: score_pvp = 2
        elif p_vp < 1.05: score_pvp = 1
    elif fii_info['Tipo'] == 'Papel':
        if p_vp < 1.01: score_pvp = 3
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

    if fii_info['Tipo'] == 'Tijolo': score_final = (score_pvp * 2) + (score_dy * 1)
    elif fii_info['Tipo'] == 'Papel': score_final = (score_pvp * 1) + (score_dy * 2)

    fii_info['Score Final'] = score_final
    return fii_info

# INTERFACE DO USUÁRIO (GRANDES MELHORIAS AQUI)
st.title('🧭 FII Compass')
st.subheader("Seu Norte no Mundo dos FIIs.")
fiis_a_analisar = [{'Ticker': 'BTLG11', 'Tipo': 'Tijolo'}, {'Ticker': 'MXRF11', 'Tipo': 'Papel'}, {'Ticker': 'VGIR11', 'Tipo': 'Papel'}]
selic_rate = get_selic_rate_from_bcb()
st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC (Anualizada)", value=f"{selic_rate:.2f}%")
st.sidebar.caption("Taxa Selic Over, fonte: Banco Central do Brasil.")
st.sidebar.markdown("---")
with st.sidebar.expander("Glossário de Métricas"):
    st.markdown("- **P/VP:** Preço da cota / Valor Patrimonial. Abaixo de 1, pode indicar que o FII está 'barato'.\n- **DY (12M):** Dividend Yield dos últimos 12 meses. O 'aluguel' anual em relação ao preço.\n- **Liq. Diária:** Liquidez média diária. Quanto maior, mais fácil é comprar e vender.\n- **Nº Cotistas:** Número de investidores. Um número crescente indica confiança no fundo.\n- **Últ. Rend.:** O valor em Reais pago no último mês por cota.")
if st.button('Analisar Meus FIIs', type="primary", use_container_width=True):
    with st.spinner('Analisando o mercado para você...'):
        lista_final = []
        for fii in fiis_a_analisar:
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
            cols_to_display = ['Ticker', 'Tipo', 'Preço Atual', 'P/VP', 'DY (12M)', 'Liq. Diária', 'Nº de Cotistas', 'Últ. Rend. (R$)', 'Score Final', 'Recomendação']
            df_display = df[cols_to_display]
            st.subheader("Ranking de Atratividade para Aporte")
            st.dataframe(df_display.style.format({'Preço Atual': 'R$ {:.2f}', 'P/VP': '{:.2f}', 'DY (12M)': '{:.2f}%', 'Liq. Diária': 'R$ {:,.0f}', 'Nº de Cotistas': '{:,}', 'Últ. Rend. (R$)': 'R$ {:.2f}'}).apply(lambda s: ['background-color: #2E8B57; color: white' if v == '🏆 Aporte do Mês' else '' for v in s], subset=['Recomendação']), use_container_width=True, hide_index=True)
        else:
            st.error("Não foi possível obter dados para nenhum dos FIIs. A fonte de dados pode estar indisponível.")
st.markdown("---")
st.caption("FII Compass | Versão 4.1 - Bugfix")
