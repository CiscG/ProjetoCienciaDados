from flask import Flask, render_template, request, jsonify
import math
import requests
import random
import time
import datetime
from tqdm import tqdm  # Nova biblioteca para a barra de progresso!

app = Flask(__name__)

# --- CONFIGURAÇÕES DE API ---
TMDB_KEY = "0b80577460d6a5ffe95ba6e9d7203155"
IGDB_CLIENT_ID = "SEU_CLIENT_ID_IGDB"
IGDB_CLIENT_SECRET = "SEU_CLIENT_SECRET_IGDB"

CACHE_API = {
    "anime_nota": None, "anime_ano": None,
    "tmdb_nota": None, "tmdb_ano": None,
    "jogos_nota": None, "jogos_ano": None
}

def gerar_mock_data(campo_analise):
    """Gera dados falsos caso a API falhe ou a internet caia"""
    return [{
        "titulo": f"[FALHA NA API] Obra {i+1}", 
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

# --- LÓGICA ESTATÍSTICA (REGRA DA RAIZ QUADRADA) ---
def calcular_estatisticas_agrupadas(dados_brutos):
    if not dados_brutos or len(dados_brutos) < 2:
        return {"erro": "Dados insuficientes."}
    
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
    
    # REGRA DA RAIZ QUADRADA (K = sqrt(N))
    k = math.ceil(math.sqrt(n))
    
    # Amplitude da classe (h)
    h = math.ceil(at / k) if k > 0 else 1
    if h == 0: h = 1
    
    classes, fi, xi, fa, fi_xi, fi_xi2 = [], [], [], [], [], []
    acumulado, inicio = 0, minimo
    
    for i in range(k):
        fim = inicio + h
        # O último intervalo deve fechar o colchete e incluir o máximo absoluto
        if i == k - 1:
            f = sum(1 for x in valores if inicio <= x <= maximo)
        else:
            f = sum(1 for x in valores if inicio <= x < fim)
        
        ponto_medio = (inicio + fim) / 2
        acumulado += f
        
        classes.append((round(inicio, 2), round(fim, 2)))
        fi.append(f)
        xi.append(round(ponto_medio, 2))
        fa.append(acumulado)
        fi_xi.append(f * ponto_medio)
        fi_xi2.append(f * (ponto_medio ** 2))
        
        inicio = fim
    
    # =========================================================================
    # ---> CORREÇÃO INSERIDA AQUI: Remoção de classes vazias no final <---
    # =========================================================================
    while len(fi) > 1 and fi[-1] == 0:
        classes.pop()
        fi.pop()
        xi.pop()
        fa.pop()
        fi_xi.pop()
        fi_xi2.pop()
        k -= 1 # Ajusta o número de classes (K) para a realidade
    # =========================================================================

    # Prevenção contra divisões por zero e cálculos de medidas de resumo
    media = sum(fi_xi) / n if n > 0 else 0
    
    pos_md = n / 2
    try:
        idx_md = next(i for i, v in enumerate(fa) if v >= pos_md)
        l_inf_md = classes[idx_md][0]
        fa_ant_md = fa[idx_md - 1] if idx_md > 0 else 0
        fi_md = fi[idx_md]
        mediana = l_inf_md + (((pos_md - fa_ant_md) * h) / fi_md) if fi_md > 0 else l_inf_md
    except StopIteration:
        mediana = media

    try:
        idx_mo = fi.index(max(fi))
        l_inf_mo = classes[idx_mo][0]
        fi_mo = fi[idx_mo]
        fi_ant = fi[idx_mo - 1] if idx_mo > 0 else 0
        fi_pos = fi[idx_mo + 1] if idx_mo < len(classes) - 1 else 0
        d1 = fi_mo - fi_ant
        d2 = fi_mo - fi_pos
        moda = l_inf_mo + ((d1 / (d1 + d2)) * h) if (d1 + d2) > 0 else xi[idx_mo]
    except ValueError:
        moda = media

    variancia = ((sum(fi_xi2) / n) - (media ** 2)) * (n / (n - 1)) if n > 1 else 0
    dp = math.sqrt(max(0, variancia))
    cv = (dp / media) * 100 if media != 0 else 0

    return {
        "n": n, "at": round(at, 2), "k": k, "h": round(h, 2),
        "classes": classes, "fi": fi, "fa": fa, "xi": xi,
        "media": round(media, 2),
        "mediana": round(mediana, 2),
        "moda": round(moda, 2),
        "variancia": round(variancia, 2),
        "dp": round(dp, 2),
        "cv": round(cv, 2),
        "itens_completos": dados_brutos if isinstance(dados_brutos[0], dict) else None
    }

# --- ROTAS DA APLICAÇÃO ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.json.get("dados", [])
    return jsonify(calcular_estatisticas_agrupadas(dados))

@app.route("/buscar_top50")
def buscar_top50():
    tipo = request.args.get("tipo", "anime")
    campo_analise = request.args.get("campo", "ano")
    chave_cache = f"{tipo}_{campo_analise}"
    
    # 1. VERIFICA O CACHE 
    if CACHE_API.get(chave_cache):
        print(f"\n✅ Retornando {len(CACHE_API[chave_cache])} itens direto do CACHE para: {chave_cache}")
        return jsonify(CACHE_API[chave_cache])

    dados_processados = []

    try:
        # 2. SE NÃO TEM CACHE, FAZ O DOWNLOAD MASSIVO
        if tipo == "anime":
            meta_itens = 7184
            paginas = math.ceil(meta_itens / 25) # ~288 páginas
            print(f"\n⏳ Iniciando download de {meta_itens} Animes. Isso leva ~7 minutos devido à limitação da API.")
            
            # Barra de progresso do TQDM
            for pagina in tqdm(range(1, paginas + 1), desc="Baixando Animes (Jikan)"):
                url = f"https://api.jikan.moe/v4/top/anime?page={pagina}"
                res = requests.get(url, timeout=15)
                
                # Se bater no limite de taxa, respira e tenta de novo
                if res.status_code == 429: 
                    time.sleep(5)
                    res = requests.get(url, timeout=15)
                    
                if res.status_code != 200:
                    break
                    
                data = res.json().get("data", [])
                if not data: break
                
                for i in data:
                    ano = i.get("year")
                    if not ano and i.get("aired", {}).get("from"):
                        ano = int(i["aired"]["from"][:4])
                    
                    nota = i.get("score", 0) * 10 if i.get("score") else 0
                    dados_processados.append({
                        "titulo": i["title"],
                        "nota": round(nota, 2),
                        "ano": ano or 0,
                        "valor": nota if campo_analise == "nota" else (ano or 0)
                    })
                    
                    if len(dados_processados) >= meta_itens:
                        break
                
                if len(dados_processados) >= meta_itens:
                    break
                    
                time.sleep(1.5) # Respirador vital para não ser banido!
                
        elif tipo == "tmdb":
            meta_itens = 9521
            paginas = math.ceil(meta_itens / 20) # ~477 páginas
            print(f"\n⏳ Iniciando download de {meta_itens} Filmes.")
            
            # Barra de progresso do TQDM
            for pagina in tqdm(range(1, paginas + 1), desc="Baixando Filmes (TMDB)"):
                url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_KEY}&language=pt-BR&page={pagina}"
                res = requests.get(url, timeout=10)
                
                if res.status_code != 200: break
                
                data = res.json().get("results", [])
                if not data: break
                
                for i in data:
                    ano = int(i.get("release_date", "0000")[:4]) if i.get("release_date") else 0
                    nota = i.get("vote_average", 0) * 10
                    
                    dados_processados.append({
                        "titulo": i.get("title"),
                        "nota": round(nota, 2),
                        "ano": ano,
                        "valor": nota if campo_analise == "nota" else ano
                    })
                    
                    if len(dados_processados) >= meta_itens:
                        break
                        
                if len(dados_processados) >= meta_itens:
                    break

        elif tipo == "jogos":
            print("\n⏳ Conectando na API do IGDB (Jogos)...")
            token = get_igdb_token()
            if not token:
                print("❌ Erro de Token IGDB.")
            else:
                headers = {'Client-ID': IGDB_CLIENT_ID, 'Authorization': f'Bearer {token}'}
                body = 'fields name, total_rating, first_release_date; sort total_rating desc; where total_rating_count > 50; limit 50;'
                res = requests.post("https://api.igdb.com/v4/games", headers=headers, data=body, timeout=10)
                if res.status_code == 200:
                    for i in res.json():
                        ano = datetime.datetime.fromtimestamp(i["first_release_date"]).year if "first_release_date" in i else 0
                        nota = i.get("total_rating", 0)
                        dados_processados.append({
                            "titulo": i.get("name"),
                            "nota": round(nota, 2),
                            "ano": ano,
                            "valor": nota if campo_analise == "nota" else ano
                        })
                    
        # 3. LIMPEZA E CACHE
        # Remove registros onde o valor analisado é zero (inválidos)
        dados_finais = [d for d in dados_processados if d["valor"] > 0]
        
        # Garante o corte exato do N solicitado
        if tipo == "anime":
            dados_finais = dados_finais[:7184]
        elif tipo == "tmdb":
            dados_finais = dados_finais[:9521]

        if not dados_finais:
            print("\n❌ Nenhuma lista retornada. Usando MOCK.")
            return jsonify(gerar_mock_data(campo_analise))
            
        CACHE_API[chave_cache] = dados_finais
        print(f"\n✅ Download Concluído! Salvando {len(dados_finais)} registros no cache da aplicação.")
        
        return jsonify(dados_finais)

    except Exception as e:
        print(f"\n⚠️ Erro Crítico: {e}. Servindo Mock Data.")
        return jsonify(gerar_mock_data(campo_analise))


if __name__ == "__main__":
    # threaded=True permite que o Flask continue respondendo enquanto faz o download gigante
    app.run(host='0.0.0.0', port=5050, debug=True, threaded=True)