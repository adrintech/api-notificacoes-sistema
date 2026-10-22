import requests
from datetime import datetime

def obter_dados_externos_reais():
    # 1. Busca temperatura real de Porto Alegre via Open-Meteo
    try:
        res_clima = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-30.033&longitude=-51.23&current=temperature_2m", timeout=3)
        temperatura = res_clima.json()["current"]["temperature_2m"]
    except:
        temperatura = 25.0 # Fallback se cair a rede

    # 2. Verifica se hoje é feriado no Brasil via Nager.Date
    try:
        ano = datetime.now().year
        res_feriado = requests.get(f"https://date.nager.at/api/v3/PublicHolidays/{ano}/BR", timeout=3)
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        eh_feriado = any(f["date"] == hoje_str for f in res_feriado.json())
    except:
        eh_feriado = False

    return {"temperatura": temperatura, "eh_feriado": eh_feriado}
def calcular_recomendacoes_fruki(perfil, clima):
    """
    Motor de scoring de produtos Fruki.
    Recebe:
      - perfil: dict com {'tipo': 'supermercado'|'padaria'|'restaurante'|...}
      - clima:  dict com {'temperatura': float, 'eh_feriado': bool} (opcional)
    Retorna: lista de dicts com produto, pontuacao (0-100) e motivo.
    """
    temperatura = clima.get('temperatura', 25.0)
    eh_feriado = clima.get('eh_feriado', False)

    tipo = (perfil.get('tipo') or 'supermercado').lower()

    # Catálogo Fruki com regras base por tipo de cliente
    catalogo = [
        {
            'produto': 'Refrigerante Guaraná Fruki 2L',
            'categorias': ['refrigerantes'],
            'peso_base': {'supermercado': 80, 'padaria': 70, 'restaurante': 60, 'bar': 50},
            'motivo_calor': 'Alta demanda de refrigerantes em dias quentes',
            'bonus_calor': 25,
        },
        {
            'produto': 'Refrigerante Citrus (Soda Limonada) 2L',
            'categorias': ['refrigerantes'],
            'peso_base': {'supermercado': 65, 'padaria': 75, 'restaurante': 70, 'bar': 80},
            'motivo_calor': 'Soda citrus é campeã de consumo no calor gaúcho',
            'bonus_calor': 30,
        },
        {
            'produto': 'Fruki Botânico 269ml (long neck)',
            'categorias': ['premium'],
            'peso_base': {'supermercado': 40, 'padaria': 55, 'restaurante': 85, 'bar': 90},
            'motivo_calor': 'Formato individual gira bem em bares e restaurantes',
            'bonus_calor': 15,
        },
        {
            'produto': 'Matte Leão 500ml (chá gelado)',
            'categorias': ['chas'],
            'peso_base': {'supermercado': 60, 'padaria': 65, 'restaurante': 50, 'bar': 70},
            'motivo_calor': 'Chá gelado tem pico de vendas acima de 28°C',
            'bonus_calor': 20,
        },
        {
            'produto': 'Água Mineral com Gás Fruki 500ml',
            'categorias': ['aguas'],
            'peso_base': {'supermercado': 70, 'padaria': 60, 'restaurante': 65, 'bar': 75},
            'motivo_calor': 'Água com gás é substituta direta do refrigerante no calor',
            'bonus_calor': 18,
        },
        {
            'produto': 'Guaraná Fruki Pack 12un (atacado)',
            'categorias': ['refrigerantes', 'atacado'],
            'peso_base': {'supermercado': 90, 'padaria': 50, 'restaurante': 45, 'bar': 40},
            'motivo_calor': 'Reposição de estoque em atacado antes de alta demanda',
            'bonus_calor': 22,
        },
    ]

    # Scoring: peso base do segmento + bônus de temperatura + bônus de feriado
    sugestoes = []
    for item in catalogo:
        score = item['peso_base'].get(tipo, 50)

        # Bônus proporcional ao calor (acima de 24°C começa a contar)
        if temperatura > 24:
            score += item['bonus_calor'] * min((temperatura - 24) / 10.0, 1.5)

        # Bônus de feriado:/reposição antecipada
        if eh_feriado:
            score += 10

        if score >= 60:
            motivo = item['motivo_calor']
            if eh_feriado:
                motivo += ' e feriado (antecipe a reposição)'
            sugestoes.append({
                'produto': item['produto'],
                'categorias': item['categorias'],
                'pontuacao': round(min(score, 100), 1),
                'motivo': motivo,
            })

    # Ordena do mais relevante para o menos
    sugestoes.sort(key=lambda s: s['pontuacao'], reverse=True)
    return sugestoes
