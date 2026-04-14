from flask import Flask, render_template, request, jsonify
import numpy as np
import json
import os
import requests
import datetime  # Necessário para converter a data do IGDB

app = Flask(__name__)

# --- CONFIGURAÇÕES DE API ---
TMDB_KEY = "SUA_CHAVE_TMDB_AQUI"
IGDB_CLIENT_ID = "SEU_CLIENT_ID_IGDB"
IGDB_CLIENT_SECRET = "SEU_CLIENT_SECRET_IGDB"

def get_igdb_token():
    """Gera o token de acesso para a API de Jogos (IGDB) via Twitch"""
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_CLIENT_SECRET}&grant_type=client_credentials"
    try:
        res = requests.post(url).json()
        return res.get("access_token")
    except:
        return None

# --- LÓGICA ESTATÍSTICA ---
def calcular_estatisticas(dados):
    if not dados or len(dados) < 2:
        return {"erro": "Dados insuficientes para análise estatística."}
    
    n = len(dados)
    dados = sorted([float(x) for x in dados])
    
    # Regra de Sturges: k = 1 + 3.322 * log10(n)
    k = int(1 + 3.322 * np.log10(n))
    minimo, maximo = min(dados), max(dados)
    amplitude_total = maximo - minimo
    h = np.ceil(amplitude_total / k) if k > 0 else 1
    if h == 0: h = 1

    classes, fi = [], []
    inicio = minimo
    for i in range(k):
        fim = inicio + h
        if i == k - 1:
            freq = sum(1 for x in dados if inicio <= x <= maximo)
        else:
            freq = sum(1 for x in dados if inicio <= x < fim)
        classes.append((round(inicio, 2), round(fim, 2)))
        fi.append(freq)
        inicio = fim

    xi = [(a + b) / 2 for a, b in classes]
    fa = np.cumsum(fi).tolist()
    
    media = np.mean(dados)
    variancia = np.var(dados, ddof=0)
    dp = np.std(dados, ddof=0)
    cv = (dp / media) * 100 if media != 0 else 0

    return {
        "n": n, "classes": classes, "fi": fi, "fa": fa, "xi": xi,
        "media": round(media, 2), "variancia": round(variancia, 2),
        "dp": round(dp, 2), "cv": round(cv, 2),
        "min": minimo, "max": maximo
    }

# --- ROTAS BÁSICAS ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.json.get("dados", [])
    return jsonify(calcular_estatisticas(dados))

# --- ROTAS DE BUSCA POR NOME ---
@app.route("/buscar_tmdb")
def buscar_tmdb():
    query = request.args.get("q")
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    res = requests.get(url).json()
    return jsonify([{"titulo": i.get("title") or i.get("name"), "nota": i.get("vote_average", 0)*10} for i in res.get("results", []) if i.get("vote_average")])

@app.route("/buscar_anime")
def buscar_anime():
    query = request.args.get("q")
    url = f"https://api.jikan.moe/v4/anime?q={query}&limit=25"
    res = requests.get(url).json()
    return jsonify([{"titulo": i["title"], "nota": i["score"]*10} for i in res.get("data", []) if i.get("score")])

@app.route("/buscar_jogos")
def buscar_jogos():
    query = request.args.get("q")
    token = get_igdb_token()
    headers = {'Client-ID': IGDB_CLIENT_ID, 'Authorization': f'Bearer {token}'}
    body = f'search "{query}"; fields name, total_rating; limit 25;'
    res = requests.post("https://api.igdb.com/v4/games", headers=headers, data=body).json()
    return jsonify([{"titulo": i["name"], "nota": i.get("total_rating", 0)} for i in res if "total_rating" in i])

# --- NOVA ROTA: BUSCAR TOP 50 (COM ANO) ---
@app.route("/buscar_top50")
def buscar_top50():
    tipo = request.args.get("tipo", "movie")
    dados = []

    try:
        if tipo == "tmdb":
            for page in [1, 2, 3]: # 3 páginas = 60 resultados
                url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_KEY}&language=pt-BR&page={page}"
                res = requests.get(url).json()
                for i in res.get("results", []):
                    ano = int(i.get("release_date", "0000")[:4]) if i.get("release_date") else 0
                    dados.append({"titulo": i.get("title"), "nota": i.get("vote_average", 0) * 10, "ano": ano})
            
        elif tipo == "anime":
            for page in [1, 2]: # 2 páginas = 50 resultados
                url = f"https://api.jikan.moe/v4/top/anime?page={page}"
                res = requests.get(url).json()
                for i in res.get("data", []):
                    ano = i.get("year")
                    if not ano and i.get("aired", {}).get("from"):
                        ano = int(i["aired"]["from"][:4])
                    dados.append({"titulo": i["title"], "nota": i.get("score", 0) * 10, "ano": ano or 0})

        elif tipo == "jogos":
            token = get_igdb_token()
            headers = {'Client-ID': IGDB_CLIENT_ID, 'Authorization': f'Bearer {token}'}
            body = 'fields name, total_rating, first_release_date; sort total_rating desc; where total_rating_count > 50; limit 50;'
            res = requests.post("https://api.igdb.com/v4/games", headers=headers, data=body).json()
            for i in res:
                ano = datetime.datetime.fromtimestamp(i["first_release_date"]).year if "first_release_date" in i else 0
                dados.append({"titulo": i["name"], "nota": i.get("total_rating", 0), "ano": ano})

        # Filtra registros sem ano válido e limita a 50
        dados_limpos = [d for d in dados if d["ano"] > 0][:50]
        return jsonify(dados_limpos)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)