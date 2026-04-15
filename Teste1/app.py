from flask import Flask, render_template, request, jsonify
import math
import requests
import random
<<<<<<< HEAD
import datetime
=======
>>>>>>> ed3036d (terminando essa merda)

app = Flask(__name__)

# --- CONFIGURAÇÕES DE API ---
TMDB_KEY = "SUA_CHAVE_TMDB_AQUI"
IGDB_CLIENT_ID = "SEU_CLIENT_ID_IGDB"
IGDB_CLIENT_SECRET = "SEU_CLIENT_SECRET_IGDB"

# Cache para evitar bloqueios da API
CACHE_API = {"anime_nota": None, "anime_ano": None, "tmdb_nota": None, "tmdb_ano": None}

def gerar_mock_data(campo):
    return [{"titulo": f"[MODO DEMO] Obra {i+1}", "nota": random.randint(70, 98), "ano": random.randint(1980, 2026), "valor": random.randint(70, 98) if campo == "nota" else random.randint(1980, 2026)} for i in range(50)]
TMDB_KEY = "0b80577460d6a5ffe95ba6e9d7203155"
IGDB_CLIENT_ID = "SEU_CLIENT_ID_IGDB"
IGDB_CLIENT_SECRET = "SEU_CLIENT_SECRET_IGDB"

# Adicione este dicionário global logo abaixo das suas configurações de API no topo do arquivo
CACHE_API = {
    "anime_nota": None,
    "anime_ano": None,
    "tmdb_nota": None,   # Adicionado por segurança para não quebrar a interface
    "tmdb_ano": None,
    "jogos_nota": None,
    "jogos_ano": None
}

def gerar_mock_data(campo_analise):
    """Gera dados de fallback dinâmicos"""
    return [{
        "titulo": f"[FALHA NA API - DADO FICTÍCIO] Obra {i+1}", 
        "nota": random.randint(70, 95), 
        "ano": random.randint(1980, 2026),
        "valor": random.randint(70, 95) if campo_analise == "nota" else random.randint(1980, 2026)
    } for i in range(50)]

def get_igdb_token():
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_CLIENT_SECRET}&grant_type=client_credentials"
    try:
        res = requests.post(url, timeout=5).json()
        return res.get("access_token")
    except:
        return None




# --- LÓGICA ESTATÍSTICA (DADOS AGRUPADOS) ---
def calcular_estatisticas_agrupadas(dados_brutos):
    if not dados_brutos or len(dados_brutos) < 2:
        return {"erro": "Dados insuficientes."}
    
    # Extração de valores (API ou Drag and Drop)
    valores = sorted([float(item['valor'] if isinstance(item, dict) else item) for item in dados_brutos])
    valores = []
    for item in dados_brutos:
        if isinstance(item, dict):
            valores.append(float(item.get('valor', item.get('ano', 0))))
        else:
            valores.append(float(item))
            
    valores = sorted(valores)
    n = len(valores)
    
    minimo, maximo = valores[0], valores[-1]
    at = maximo - minimo
    
    # Regra da Raiz (n=50 -> k=8)
    k_real = math.sqrt(n)
    k = math.ceil(k_real)
    h = math.ceil(at / k_real) if k_real > 0 else 1
    k_real = math.sqrt(n)
    k = math.ceil(k_real)
    h = math.ceil(at / k_real) if k_real > 0 else 1
    if h == 0: h = 1
    
    classes, fi, xi, fa, fi_xi, fi_xi2 = [], [], [], [], [], []
    acumulado, inicio = 0, minimo
    
    for i in range(k):
        fim = inicio + h
        # Lógica de fronteira
        f = sum(1 for x in valores if inicio <= x <= maximo) if i == k - 1 else sum(1 for x in valores if inicio <= x < fim)
        
        ponto_medio = (inicio + fim) / 2
        acumulado += f
        if i == k - 1:
            f = sum(1 for x in valores if inicio <= x <= maximo)
        else:
            f = sum(1 for x in valores if inicio <= x < fim)
        
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
        
        inicio = fim

    # ---> NOVO: Remoção de classes vazias no final da tabela <---
    while len(fi) > 1 and fi[-1] == 0:
        classes.pop()
        fi.pop()
        xi.pop()
        fa.pop()
        fi_xi.pop()
        fi_xi2.pop()
        k -= 1 # Ajusta o K virtualmente
    
    # Cálculos Estatísticos
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
    fi_md = fi[idx_md]
    mediana = l_inf_md + (((pos_md - fa_ant_md) * h) / fi_md) if fi_md > 0 else l_inf_md

    idx_mo = fi.index(max(fi))
    l_inf_mo = classes[idx_mo][0]
    fi_mo = fi[idx_mo]
    fi_ant = fi[idx_mo - 1] if idx_mo > 0 else 0
    fi_pos = fi[idx_mo + 1] if idx_mo < len(classes) - 1 else 0
    d1 = fi_mo - fi_ant
    d2 = fi_mo - fi_pos
    moda = l_inf_mo + ((d1 / (d1 + d2)) * h) if (d1 + d2) > 0 else xi[idx_mo]

    variancia = ((sum(fi_xi2) / n) - (media ** 2)) * (n / (n - 1)) if n > 1 else 0
    dp = math.sqrt(max(0, variancia))
    cv = (dp / media) * 100 if media != 0 else 0

    return {
        "n": n, "at": round(at, 2), "k": k, "h": round(h, 2),
        "classes": classes, "fi": fi, "fa": fa, "xi": [round(x, 2) for x in xi],
        "media": round(media, 2),
        "mediana": round(mediana, 2),
        "moda": round(moda, 2),
        "variancia": round(variancia, 2),
        "dp": round(dp, 2),
        "cv": round(cv, 2),
        "valores_processados": valores,
        "itens_completos": dados_brutos if isinstance(dados_brutos[0], dict) else None
    }

@app.route("/")
def index(): return render_template("index.html")
def index():
    return render_template("index.html")

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
    tipo = request.args.get("tipo", "anime")
    campo_analise = request.args.get("campo", "ano")
    
    chave_cache = f"{tipo}_{campo_analise}"
    
    # 1. VERIFICA O CACHE PRIMEIRO
    if chave_cache in CACHE_API and CACHE_API[chave_cache] is not None:
        print(f"✅ Retornando dados REAIS do Cache para: {chave_cache}")
        return jsonify(CACHE_API[chave_cache])

    dados_processados = []

    try:
        # 2. SE NÃO TEM CACHE, CHAMA A API
        if tipo == "anime":
            print("⏳ Conectando na API do Jikan (MyAnimeList)...")
            headers = {'User-Agent': 'ProjetoFaculdadeCienciaDados/1.0'}
            
            for pagina in [1, 2]:
                url = f"https://api.jikan.moe/v4/top/anime?page={pagina}"
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                
                for i in res.json().get("data", []):
                    ano = i.get("year")
                    if not ano and i.get("aired", {}).get("from"):
                        ano = int(i["aired"]["from"][:4])
                    
                    dados_processados.append({
                        "titulo": i["title"],
                        "nota": i.get("score", 0) * 10,
                        "ano": ano or 0,
                        "valor": i.get("score", 0) * 10 if campo_analise == "nota" else (ano or 0)
                    })
                    
        # --- NOVA LÓGICA DO TMDB (FILMES) ---
        elif tipo == "tmdb":
            print("⏳ Conectando na API do TMDB (Filmes)...")
            # TMDB retorna 20 itens por página. 3 páginas = 60 itens (depois cortamos para 50)
            for pagina in [1, 2, 3]:
                url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_KEY}&language=pt-BR&page={pagina}"
                res = requests.get(url, timeout=10)
                res.raise_for_status() # Vai acusar erro no terminal se a sua chave TMDB_KEY estiver errada
                
                for i in res.json().get("results", []):
                    ano = int(i.get("release_date", "0000")[:4]) if i.get("release_date") else 0
                    nota = i.get("vote_average", 0) * 10
                    
                    dados_processados.append({
                        "titulo": i.get("title"),
                        "nota": round(nota, 2),
                        "ano": ano,
                        "valor": nota if campo_analise == "nota" else ano
                    })

        # --- NOVA LÓGICA DO IGDB (JOGOS) ---
        elif tipo == "jogos":
            print("⏳ Conectando na API do IGDB (Jogos)...")
            token = get_igdb_token()
            if not token:
                print("❌ Erro de Token IGDB: Verifique seu CLIENT_ID e CLIENT_SECRET.")
            else:
                headers = {'Client-ID': IGDB_CLIENT_ID, 'Authorization': f'Bearer {token}'}
                # IGDB permite buscar os 50 de uma vez só com 'limit 50'
                body = 'fields name, total_rating, first_release_date; sort total_rating desc; where total_rating_count > 50; limit 50;'
                res = requests.post("https://api.igdb.com/v4/games", headers=headers, data=body, timeout=10)
                res.raise_for_status()
                
                for i in res.json():
                    # O IGDB retorna a data em Unix Timestamp, precisamos converter
                    ano = datetime.datetime.fromtimestamp(i["first_release_date"]).year if "first_release_date" in i else 0
                    nota = i.get("total_rating", 0)
                    
                    dados_processados.append({
                        "titulo": i.get("name"),
                        "nota": round(nota, 2),
                        "ano": ano,
                        "valor": nota if campo_analise == "nota" else ano
                    })

        # ==========================================

        if not dados_processados:
            print("❌ API retornou vazio. Usando MOCK.")
            return jsonify(gerar_mock_data(campo_analise))
            
        # 3. SALVA OS DADOS REAIS NO CACHE PARA A PRÓXIMA VEZ
        dados_finais = dados_processados[:50] # Garante que são exatamente 50
        CACHE_API[chave_cache] = dados_finais
        print(f"✅ Dados REAIS salvos no cache com sucesso para {chave_cache}!")
        
        return jsonify(dados_finais)

    except Exception as e:
        # Agora o erro cai aqui corretamente sem corromper o cache!
        print(f"⚠️ Erro Crítico de Conexão: {e}. Servindo Mock Data.")
        return jsonify(gerar_mock_data(campo_analise))


if __name__ == "__main__":
    app.run(debug=True)
