import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# === CONFIG STREAMLIT ===
st.set_page_config(page_title="Odds Estratégicas", layout="wide")
st.title("Consulta de Odds Estratégicas (Bet365 + Betano) via API-Football")

# === CHAVE DE API ===
API_KEY = 'f8004fe5cca0e75109a44ae6b4cdd9a2'
HEADERS = {'x-apisports-key': API_KEY}

# === INPUT DE DATA ===
data_input = st.date_input("Selecione a data da partida", datetime.today()).strftime("%Y-%m-%d")

# === BUSCAR PARTIDAS COM ODDS ===
st.info(f"Buscando partidas com odds para {data_input}...")
url_odds = f"https://v3.football.api-sports.io/odds?date={data_input}"
resp = requests.get(url_odds, headers=HEADERS)
odds_response = resp.json().get('response', [])

if not odds_response:
    st.warning("Nenhuma partida com odds disponíveis nesta data.")
    st.stop()

# === LISTAR PARTIDAS ===
partidas = []
for jogo in odds_response:
    fixture_id = jogo['fixture']['id']
    data_hora = datetime.fromisoformat(jogo['fixture']['date']).strftime('%d/%m %H:%M')

    # Buscar nomes dos times
    url_fixture = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
    fixture_resp = requests.get(url_fixture, headers=HEADERS)
    dados_fixture = fixture_resp.json()['response'][0]
    home = dados_fixture['teams']['home']['name']
    away = dados_fixture['teams']['away']['name']

    jogo['teams'] = {'home': home, 'away': away}
    partidas.append({
        'label': f"{data_hora} | {home} x {away}",
        'value': fixture_id,
        'jogo': jogo
    })

# === SELECIONAR PARTIDA ===
options = [p['label'] for p in partidas]
selecionada = st.selectbox("Escolha a partida:", options)

if selecionada:
    jogo_escolhido = next(p['jogo'] for p in partidas if p['label'] == selecionada)
    home = jogo_escolhido['teams']['home']
    away = jogo_escolhido['teams']['away']
    fixture_id = jogo_escolhido['fixture']['id']

    st.subheader(f"Odds filtradas: {home} x {away} (Bet365 e Betano)")

    # === MERCADOS RELEVANTES (somente jogo) ===
    mercados_permitidos = [
        "Match Winner", "1X2",
        "Asian Handicap",
        "Over/Under", "Goals Over/Under",
        "Shots", "Shots on Target",
        "Fouls", "Cards",
        "Corners", "Offsides",
        "Both Teams To Score", "BTTS"
    ]

    palavras_proibidas = [
        "player", "scorer", "assist", "passes", "shots on", "shots by", 
        "goals by", "cards by", "player to", "team to", "1st to"
    ]

    casas_permitidas = ['bet365', 'betano']

    # === COLETAR E FILTRAR ODDS ===
    csv_data = []
    for bookmaker in jogo_escolhido['bookmakers']:
        nome_casa = bookmaker['name'].lower()
        if nome_casa not in casas_permitidas:
            continue

        for bet in bookmaker['bets']:
            nome_mercado = bet['name'].lower()

            if any(p.lower() in nome_mercado for p in mercados_permitidos) and not any(ban in nome_mercado for ban in palavras_proibidas):
                for val in bet['values']:
                    csv_data.append({
                        'Casa': bookmaker['name'],
                        'Mercado': bet['name'],
                        'Linha': val['value'],
                        'Odd': val['odd']
                    })

    # === MOSTRAR TABELA E DOWNLOAD ===
    if csv_data:
        df = pd.DataFrame(csv_data)
        st.dataframe(df, use_container_width=True)

        csv_file = df.to_csv(index=False).encode('utf-8')
        nome_arquivo = f"odds_{home}_vs_{away}_{data_input}_bet365_betano.csv".replace(' ', '_').replace('/', '-')
        st.download_button(
            label="📥 Baixar arquivo CSV",
            data=csv_file,
            file_name=nome_arquivo,
            mime='text/csv'
        )
    else:
        st.warning("Nem Bet365 nem Betano possuem mercados relevantes para essa partida.")