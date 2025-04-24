import requests
import pandas as pd
from datetime import datetime
from google.colab import files

# API Key
API_KEY = 'f8004fe5cca0e75109a44ae6b4cdd9a2'
headers = {'x-apisports-key': API_KEY}

# === Entrada: Data ===
data_input = input("Digite a data desejada (YYYY-MM-DD): ").strip()

# Buscar partidas com odds
url_odds = f"https://v3.football.api-sports.io/odds?date={data_input}"
resp = requests.get(url_odds, headers=headers)
odds_response = resp.json()['response']

if not odds_response:
    print("Nenhuma partida com odds disponíveis para essa data.")
else:
    print("\n=== Partidas com Odds ===")
    jogos_completos = []

    for i, jogo in enumerate(odds_response):
        fixture_id = jogo['fixture']['id']
        data_hora = datetime.fromisoformat(jogo['fixture']['date']).strftime('%d/%m %H:%M')

        # Buscar nomes dos times
        fixture_url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
        fixture_resp = requests.get(fixture_url, headers=headers)
        fixture_info = fixture_resp.json()['response'][0]
        home = fixture_info['teams']['home']['name']
        away = fixture_info['teams']['away']['name']

        print(f"{i+1}. ID: {fixture_id} | {data_hora} | {home} x {away}")
        jogo['teams'] = {'home': home, 'away': away}
        jogos_completos.append(jogo)

    # Escolher partida
    while True:
        try:
            idx = int(input("\nDigite o número da partida para ver as odds e exportar CSV: ")) - 1
            jogo_escolhido = jogos_completos[idx]
            break
        except (ValueError, IndexError):
            print("Número inválido. Tente novamente.")

    fixture_id = jogo_escolhido['fixture']['id']
    home = jogo_escolhido['teams']['home']
    away = jogo_escolhido['teams']['away']

    print(f"\n=== Odds para {home} x {away} ===")
    csv_data = []

    for bookmaker in jogo_escolhido['bookmakers']:
        casa = bookmaker['name']
        for bet in bookmaker['bets']:
            mercado = bet['name']
            for val in bet['values']:
                linha = val['value']
                odd = val['odd']
                print(f"{casa} | {mercado} | {linha} -> {odd}")
                csv_data.append({
                    'Casa': casa,
                    'Mercado': mercado,
                    'Linha': linha,
                    'Odd': odd
                })

    # Salvar e fazer download
    df = pd.DataFrame(csv_data)
    filename = f"/content/odds_{home}_vs_{away}_{data_input}.csv".replace(' ', '_').replace('/', '-')
    df.to_csv(filename, index=False)
    print(f"\nArquivo CSV pronto para download:")
    files.download(filename)
