from flask import Flask, render_template, request, jsonify
import math
import requests
import random
import datetime

app = Flask(__name__)

# --- CONFIGURAÇÕES DE API ---
TMDB_KEY = "SUA_CHAVE_TMDB_AQUI"
IGDB_CLIENT_ID = "SEU_CLIENT_ID_IGDB"
IGDB_CLIENT_SECRET = "SEU_CLIENT_SECRET_IGDB"

# Cache para evitar bloqueios da API
CACHE_API = {"anime_nota": None, "anime_ano": None, "tmdb_nota": None, "tmdb_ano": None}

def gerar_mock_data(campo):
    return [{"titulo": f"[MODO DEMO] Obra {i+1}", "nota": random.randint(70, 98), "ano": random.randint(1980, 2026), "valor": random.randint(70, 98) if campo == "nota" else random.randint(1980, 2026)} for i in range(50)]

# --- LÓGICA ESTATÍSTICA (DADOS AGRUPADOS) ---
def calcular_estatisticas_agrupadas(dados_brutos):
    if not dados_brutos or len(dados_brutos) < 2:
        return {"erro": "Dados insuficientes."}
    
    # Extração de valores (API ou Drag and Drop)
    valores = sorted([float(item['valor'] if isinstance(item, dict) else item) for item in dados_brutos])
    n = len(valores)
    
    minimo, maximo = valores[0], valores[-1]
    at = maximo - minimo
    
    # Regra da Raiz (n=50 -> k=8)
    k_real = math.sqrt(n)
    k = math.ceil(k_real)
    h = math.ceil(at / k_real) if k_real > 0 else 1
    
    classes, fi, xi, fa, fi_xi, fi_xi2 = [], [], [], [], [], []
    acumulado, inicio = 0, minimo
    
    for i in range(k):
        fim = inicio + h
        # Lógica de fronteira
        f = sum(1 for x in valores if inicio <= x <= maximo) if i == k - 1 else sum(1 for x in valores if inicio <= x < fim)
        
        ponto_medio = (inicio + fim) / 2
        acumulado += f
        classes.append((round(inicio, 2), round(fim, 2)))
        fi.append(f)
        xi.append(ponto_medio)
        fa.append(acumulado)
        fi_xi.append(f * ponto_medio)
        fi_xi2.append(f * (ponto_medio ** 2))
        inicio = fim

    # REMOÇÃO DE CLASSE INVÁLIDA (Frequência Zero no final)
    while len(fi) > 1 and fi[-1] == 0:
        classes.pop(); fi.pop(); xi.pop(); fa.pop(); fi_xi.pop(); fi_xi2.pop()

    # Cálculos para Dados Agrupados
    media = sum(fi_xi) / n
    pos_md = n / 2
    idx_md = next(i for i, v in enumerate(fa) if v >= pos_md)
    l_inf_md = classes[idx_md][0]
    fa_ant_md = fa[idx_md - 1] if idx_md > 0 else 0
    mediana = l_inf_md + (((pos_md - fa_ant_md) * h) / fi[idx_md]) if fi[idx_md] > 0 else l_inf_md

    idx_mo = fi.index(max(fi))
    l_inf_mo = classes[idx_mo][0]
    d1 = fi[idx_mo] - (fi[idx_mo-1] if idx_mo > 0 else 0)
    d2 = fi[idx_mo] - (fi[idx_mo+1] if idx_mo < len(classes)-1 else 0)
    moda = l_inf_mo + ((d1 / (d1 + d2)) * h) if (d1 + d2) > 0 else xi[idx_mo]

    variancia = ((sum(fi_xi2) / n) - (media ** 2)) * (n / (n - 1)) # Amostral
    dp = math.sqrt(max(0, variancia))

    return {
        "n": n, "at": round(at, 2), "classes": classes, "fi": fi, "fa": fa, "xi": [round(x, 2) for x in xi],
        "media": round(media, 2), "mediana": round(mediana, 2), "moda": round(moda, 2),
        "variancia": round(variancia, 2), "dp": round(dp, 2), "cv": round((dp/media)*100, 2) if media != 0 else 0,
        "itens_completos": dados_brutos if isinstance(dados_brutos[0], dict) else None
    }

@app.route("/")
def index(): return render_template("index.html")

@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.json.get("dados", [])
    return jsonify(calcular_estatisticas_agrupadas(dados))

@app.route("/buscar_top50")
def buscar_top50():
    tipo, campo = request.args.get("tipo", "anime"), request.args.get("campo", "ano")
    chave = f"{tipo}_{campo}"
    if CACHE_API.get(chave): return jsonify(CACHE_API[chave])

    dados_proc = []
    try:
        if tipo == "anime":
            # Paginação para evitar erro 400
            for p in [1, 2]:
                res = requests.get(f"https://api.jikan.moe/v4/top/anime?page={p}", timeout=10).json()
                for i in res.get("data", []):
                    ano = i.get("year") or (int(i["aired"]["from"][:4]) if i.get("aired", {}).get("from") else 0)
                    nota = round(i.get("score", 0) * 10, 2)
                    dados_proc.append({"titulo": i["title"], "nota": nota, "ano": ano, "valor": nota if campo == "nota" else ano})
        
        if not dados_proc: return jsonify(gerar_mock_data(campo))
        CACHE_API[chave] = dados_proc[:50]
        return jsonify(CACHE_API[chave])
    except: return jsonify(gerar_mock_data(campo))

if __name__ == "__main__": app.run(debug=True)