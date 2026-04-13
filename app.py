from flask import Flask, render_template, request, jsonify
import numpy as np
import json
import os
import requests

app = Flask(__name__)

DATA_PATH = "data/catalogo.json"
TMDB_KEY = "SUA_CHAVE_AQUI"  # coloque sua chave

# ------------------ CARREGAR DADOS LOCAIS ------------------
def carregar_catalogo():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []

# ------------------ CÁLCULO ESTATÍSTICO ------------------
def calcular(dados):
    n = len(dados)

    k = int(1 + 3.3 * np.log10(n))

    minimo = min(dados)
    maximo = max(dados)
    amplitude = maximo - minimo
    h = int(np.ceil(amplitude / k))

    classes = []
    fi = []

    inicio = minimo

    for i in range(k):
        fim = inicio + h
        freq = sum(1 for x in dados if inicio <= x < fim)
        classes.append((inicio, fim))
        fi.append(freq)
        inicio = fim

    xi = [(a + b) / 2 for a, b in classes]
    fixi = [f * x for f, x in zip(fi, xi)]
    fixi2 = [f * (x**2) for f, x in zip(fi, xi)]
    fa = np.cumsum(fi).tolist()

    media = sum(fixi) / sum(fi)
    variancia = (sum(fixi2) / sum(fi)) - (media ** 2)
    dp = np.sqrt(variancia)
    cv = (dp / media) * 100

    # -------- Curva normal --------
    x_vals = np.linspace(minimo, maximo, 100)

    if dp == 0:
       normal_y = [0]*100
    else:
       pdf = (1 / (dp * np.sqrt(2 * np.pi))) * np.exp(-((x_vals - media) ** 2) / (2 * dp ** 2))
       normal_y = pdf * sum(fi) * h

    return {
        "classes": classes,
        "fi": fi,
        "fa": fa,
        "xi": xi,
        "fixi": fixi,
        "fixi2": fixi2,
        "media": round(media, 2),
        "variancia": round(variancia, 2),
        "dp": round(dp, 2),
        "cv": round(cv, 2),
        "normal_x": x_vals.tolist(),
        "normal_y": normal_y.tolist() if hasattr(normal_y, 'tolist') else normal_y
    }

# ------------------ ROTAS ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/catalogo")
def catalogo():
    return jsonify(carregar_catalogo())

@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.json["dados"]
    return jsonify(calcular(dados))

# -------- TMDB --------
@app.route("/tmdb")
def tmdb():
    tipo = request.args.get("tipo", "movie")

    url = f"https://api.themoviedb.org/3/{tipo}/popular?api_key={TMDB_KEY}&language=pt-BR&page=1"
    res = requests.get(url).json()

    dados = []
    for item in res.get("results", []):
        nota = item.get("vote_average", 0) * 10
        dados.append({
            "titulo": item.get("title") or item.get("name"),
            "nota": nota,
            "tipo": tipo
        })

    return jsonify(dados)

# -------- ANIME (Jikan) --------
@app.route("/anime")
def anime():
    url = "https://api.jikan.moe/v4/top/anime"
    res = requests.get(url).json()

    dados = []
    for item in res.get("data", [])[:20]:
        if item.get("score"):
            dados.append({
                "titulo": item["title"],
                "nota": item["score"] * 10,
                "tipo": "anime"
            })

    return jsonify(dados)

if __name__ == "__main__":
    app.run(debug=True)