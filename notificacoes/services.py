import requests
from datetime import datetime

def obter_dados_externos_reais():
    # 1. Busca temperatura real de Porto Alegre via Open-Meteo (Gratuita e sem API Key)
    try:
        res_clima = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-30.033&longitude=-51.23&current=temperature_2m", timeout=3)
        temperatura = res_clima.json()["current"]["temperature_2m"]
    except:
        temperatura = 25.0 # Valor padrão caso ocorra falha de rede

    # 2. Verifica se hoje é feriado no Brasil via Nager.Date (Gratuita e sem API Key)
    try:
        ano = datetime.now().year
        res_feriado = requests.get(f"https://date.nager.at/api/v3/PublicHolidays/{ano}/BR", timeout=3)
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        eh_feriado = any(f["date"] == hoje_str for f in res_feriado.json())
    except:
        eh_feriado = False

    return {"temperatura": temperatura, "eh_feriado": eh_feriado}

