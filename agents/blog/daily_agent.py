"""
Gaming Blog + Pinterest Agent — Powered by Google Gemini (GRATIS)
Corre diariamente via GitHub Actions:
1. En el PRIMER run: elige el nombre del blog y lo guarda
2. Encuentra keywords gaming con baja competencia
3. Escribe artículo SEO completo con links de afiliados
4. Publica en GitHub Pages automáticamente
5. Genera 5 pins de Pinterest para ese artículo
6. Publica los pins en Pinterest

Estructura del blog en GitHub Pages:
gaming-income-os/
  docs/          ← GitHub Pages sirve desde aquí
    index.html
    _posts/
    assets/
"""

import os, json, re, time, base64, requests
from datetime import datetime
from pathlib import Path

# ── API Keys ────────────────────────────────────────────────
GROQ_KEY         = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN     = os.environ["GITHUB_TOKEN"]          # automático en Actions
GITHUB_REPO      = os.environ["GITHUB_REPO"]           # ej: "tuusuario/gaming-income-os"
PINTEREST_TOKEN  = os.environ.get("PINTEREST_TOKEN", "") # opcional al inicio
AMAZON_TAG       = os.environ.get("AMAZON_AFFILIATE_TAG", "gamingincome-20")

GROQ_API   = "https://api.groq.com/openai/v1/chat/completions"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"

# ── Gemini helper ────────────────────────────────────────────
def gemini(prompt, temperature=0.7):
    key = GROQ_KEY
    print(f"  DEBUG key length: {len(key)}, starts: {key[:4]}")
    r = requests.post(GROQ_API,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": temperature, "max_tokens": 2000})
    print(f"  DEBUG status: {r.status_code}")
    print(f"  DEBUG response: {r.text[:200]}")
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"```json|```", "", text).strip()

def gemini_json(prompt):
    return json.loads(gemini(prompt))

# ── GitHub Pages helpers ─────────────────────────────────────
def github_get(path):
    r = requests.get(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"})
    return r.json() if r.status_code == 200 else None

def github_put(path, content, message, sha=None):
    body = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha:
        body["sha"] = sha
    r = requests.put(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"},
        json=body)
    r.raise_for_status()
    return r.json()

def github_get_file_sha(path):
    existing = github_get(path)
    return existing.get("sha") if existing and "sha" in existing else None

# ── Blog name chooser (runs once) ─────────────────────────────
def choose_blog_name():
    """Elige el mejor nombre para el blog gaming basado en SEO."""
    result = gemini_json("""Eres experto en SEO y dominios web para blogs de gaming.
Elige el MEJOR nombre para un blog de gaming enfocado en reseñas, guías y recomendaciones
de productos gaming con links de afiliados de Amazon.

Criterios: memorable, fácil de escribir, bueno para SEO, disponible como .com probablemente,
relacionado con gaming pero no demasiado específico para poder crecer.

Responde SOLO JSON sin markdown:
{
  "blog_name": "NombreDelBlog",
  "domain": "nombredelBlog.com",
  "tagline": "tagline corto del blog en español",
  "description": "descripción SEO del blog (160 chars max)",
  "focus": "descripción de qué cubre el blog",
  "amazon_niche": "gaming"
}

Ejemplos de buenos nombres: PixelGearPro, LevelUpGadgets, GamingPicksPro, ArenaGearHub""")
    return result

# ── Keyword research ─────────────────────────────────────────
def find_keyword():
    today = datetime.now().strftime("%Y-%m-%d")
    return gemini_json(f"""Hoy es {today}. Eres experto en SEO para blogs de gaming y afiliados de Amazon.
Encuentra UNA keyword gaming perfecta para escribir HOY:
- Intención de compra alta (alguien buscando comprar algo)
- Competencia baja-media (blog nuevo puede posicionar)
- Volumen decente (500-5000 búsquedas/mes estimado)
- Relacionada con productos en Amazon

Responde SOLO JSON sin markdown:
{{
  "keyword": "la keyword principal",
  "monthly_searches": 1200,
  "difficulty": "baja",
  "intent": "compra",
  "article_title": "título del artículo SEO en español (con la keyword)",
  "amazon_products": ["tipo de producto 1", "tipo de producto 2", "tipo de producto 3"],
  "reason": "por qué esta keyword es buena ahora mismo"
}}

Ejemplos de buenas keywords: "mejor ratón gaming 2025", "auriculares gaming baratos menos de 50 euros",
"silla gaming ergonómica para estudiantes", "teclado mecánico gaming principiantes" """)

# ── Article writer ───────────────────────────────────────────
def write_article(keyword_data, blog_data):
    amazon_tag = AMAZON_TAG
    return gemini(f"""Escribe un artículo SEO completo en español para el blog "{blog_data['blog_name']}".

Keyword objetivo: {keyword_data['keyword']}
Título: {keyword_data['article_title']}
Productos a recomendar: {', '.join(keyword_data['amazon_products'])}
Tag de afiliado Amazon: {amazon_tag}

FORMATO: HTML limpio listo para publicar en blog. Incluye:
- <h1> con el título exacto
- Introducción de 100 palabras con la keyword
- Al menos 4 secciones <h2> con contenido útil
- Lista de productos recomendados con links de afiliado Amazon:
  formato: <a href="https://amazon.es/s?k=PRODUCTO&tag={amazon_tag}">Ver precio en Amazon</a>
- Sección FAQ con 3 preguntas frecuentes
- Conclusión con call to action
- Meta description en comentario HTML al inicio: <!-- META: descripción aquí -->
- Total: 900-1200 palabras
- NO incluir DOCTYPE ni <html> ni <head> — solo el contenido del artículo

Escribe en español natural, útil y que ayude genuinamente al lector a tomar una decisión de compra.""",
    temperature=0.6)

# ── Pinterest pins generator ─────────────────────────────────
def generate_pins(keyword_data, article_url, blog_data):
    return gemini_json(f"""Genera 5 pins de Pinterest para promocionar este artículo de blog gaming.

Artículo: {keyword_data['article_title']}
URL: {article_url}
Blog: {blog_data['blog_name']} - {blog_data['tagline']}

Responde SOLO JSON sin markdown:
{{
  "pins": [
    {{
      "title": "título del pin (max 100 chars)",
      "description": "descripción del pin con keywords (max 500 chars), menciona el blog",
      "image_prompt": "detailed english prompt for generating a Pinterest-style gaming infographic image, 2:3 ratio, bright colors, text overlay space",
      "board": "nombre del tablero de Pinterest donde publicarlo"
    }}
  ]
}}

Genera 5 pins variados: infográfico, lista, comparativa, tip rápido, pregunta.
Boards sugeridos: Gaming Gear, Best Gaming Products, Gaming Tips, Gaming Setup Ideas.""")

# ── Pinterest publisher ──────────────────────────────────────
def publish_pin(pin_data, article_url):
    if not PINTEREST_TOKEN:
        print("  ⏭ Pinterest token no configurado, guardando pin para subida manual")
        return False
    try:
        r = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {PINTEREST_TOKEN}",
                     "Content-Type": "application/json"},
            json={
                "title": pin_data["title"],
                "description": pin_data["description"],
                "link": article_url,
                "media_source": {"source_type": "image_url",
                                 "url": "https://via.placeholder.com/600x900/1a1a2e/00ff88?text=Gaming"}
            }
        )
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"  ⚠ Error publicando pin: {e}")
        return False

# ── GitHub Pages site builder ─────────────────────────────────
def ensure_site_structure(blog_data):
    """Crea la estructura base del blog si no existe."""
    index_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{blog_data['blog_name']} - {blog_data['tagline']}</title>
<meta name="description" content="{blog_data['description']}">
<style>
  :root {{--accent:#00ff88;--bg:#0a0a0f;--card:#12121a;--text:#e2e2f0;--muted:#6b6b8a}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
  header{{background:#0f0f18;border-bottom:1px solid #1e1e2e;padding:20px;text-align:center}}
  header h1{{font-size:2rem;font-weight:900;color:var(--accent)}}
  header p{{color:var(--muted);font-size:0.9rem;margin-top:6px}}
  main{{max-width:900px;margin:40px auto;padding:0 20px}}
  .articles{{display:grid;gap:20px}}
  article{{background:var(--card);border:1px solid #1e1e2e;border-radius:12px;padding:24px}}
  article h2{{font-size:1.2rem;margin-bottom:8px}}
  article h2 a{{color:var(--text);text-decoration:none}}
  article h2 a:hover{{color:var(--accent)}}
  article .meta{{color:var(--muted);font-size:0.8rem;margin-bottom:10px}}
  article p{{color:var(--muted);font-size:0.9rem}}
  footer{{text-align:center;padding:40px;color:var(--muted);font-size:0.8rem;border-top:1px solid #1e1e2e;margin-top:60px}}
  .tag{{background:rgba(0,255,136,0.1);color:var(--accent);border:1px solid rgba(0,255,136,0.3);padding:2px 10px;border-radius:20px;font-size:0.75rem}}
</style>
</head>
<body>
<header>
  <h1>🎮 {blog_data['blog_name']}</h1>
  <p>{blog_data['tagline']}</p>
</header>
<main>
  <div id="articles" class="articles">
    <p style="color:var(--muted);text-align:center;padding:40px">Cargando artículos...</p>
  </div>
</main>
<footer>
  <p>{blog_data['blog_name']} © {datetime.now().year} · Afiliado de Amazon · Los precios pueden variar</p>
  <p style="margin-top:8px;font-size:0.72rem">Como Asociado de Amazon, obtenemos ingresos por las compras adscritas que cumplen los requisitos aplicables.</p>
</footer>
<script>
  // Carga artículos desde el índice
  fetch('/gaming-income-os/docs/articles/index.json')
    .then(r=>r.json())
    .then(data=>{{
      const c=document.getElementById('articles');
      if(!data.articles||!data.articles.length){{c.innerHTML='<p style="color:var(--muted);text-align:center;padding:40px">Pronto habrá artículos aquí.</p>';return}}
      c.innerHTML=data.articles.slice(0,20).map(a=>`
        <article>
          <div class="meta">${{a.date}} · <span class="tag">Gaming</span></div>
          <h2><a href="${{a.url}}">${{a.title}}</a></h2>
          <p>${{a.excerpt}}</p>
        </article>`).join('');
    }}).catch(()=>{{document.getElementById('articles').innerHTML='<p style="color:var(--muted);text-align:center;padding:40px">Artículos próximamente.</p>'}});
</script>
</body>
</html>"""

    sha = github_get_file_sha("docs/index.html")
    github_put("docs/index.html", index_html, f"🎮 Init: {blog_data['blog_name']}", sha)
    print(f"  ✓ Homepage creada: {blog_data['blog_name']}")

def publish_article(article_html, keyword_data, blog_data):
    """Publica el artículo en GitHub Pages y actualiza el índice."""
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", keyword_data["keyword"].lower()).strip("-")
    filename = f"docs/articles/{today}-{slug}.html"
    repo_name = GITHUB_REPO.split("/")[1]
    article_url = f"https://{GITHUB_REPO.split('/')[0]}.github.io/{repo_name}/articles/{today}-{slug}.html"

    # Extract meta description
    meta_match = re.search(r'<!--\s*META:\s*(.+?)\s*-->', article_html)
    meta_desc = meta_match.group(1) if meta_match else keyword_data["keyword"]
    excerpt = meta_desc[:160]

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{keyword_data['article_title']} - {blog_data['blog_name']}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{keyword_data['article_title']}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<style>
  :root{{--accent:#00ff88;--bg:#0a0a0f;--card:#12121a;--text:#e2e2f0;--muted:#6b6b8a}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.8}}
  header{{background:#0f0f18;border-bottom:1px solid #1e1e2e;padding:16px 20px}}
  header a{{color:var(--accent);text-decoration:none;font-weight:700}}
  main{{max-width:760px;margin:40px auto;padding:0 20px}}
  h1{{font-size:1.9rem;font-weight:900;line-height:1.2;margin-bottom:16px;color:var(--text)}}
  h2{{font-size:1.3rem;font-weight:700;margin:32px 0 12px;color:var(--accent)}}
  h3{{font-size:1.1rem;font-weight:700;margin:24px 0 8px}}
  p{{margin-bottom:16px;color:#c4c4e0}}
  ul,ol{{margin:12px 0 16px 24px;color:#c4c4e0}}
  li{{margin-bottom:6px}}
  a{{color:var(--accent)}}
  .affiliate-btn{{display:inline-block;background:rgba(0,255,136,0.1);border:1px solid var(--accent);color:var(--accent);padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:700;margin:8px 0;transition:all 0.2s}}
  .affiliate-btn:hover{{background:rgba(0,255,136,0.2)}}
  .product-card{{background:var(--card);border:1px solid #1e1e2e;border-radius:12px;padding:20px;margin:16px 0}}
  .faq-item{{background:var(--card);border:1px solid #1e1e2e;border-radius:10px;padding:16px;margin:10px 0}}
  .faq-item h3{{margin:0 0 8px;color:var(--text);font-size:1rem}}
  .meta{{color:var(--muted);font-size:0.8rem;margin-bottom:24px}}
  .disclaimer{{background:rgba(255,255,255,0.03);border:1px solid #1e1e2e;border-radius:8px;padding:12px 16px;margin-top:40px;color:var(--muted);font-size:0.75rem}}
  footer{{text-align:center;padding:40px;color:var(--muted);font-size:0.8rem;border-top:1px solid #1e1e2e;margin-top:60px}}
</style>
</head>
<body>
<header><a href="/{repo_name}/">← {blog_data['blog_name']}</a></header>
<main>
  <div class="meta">📅 {today} · 🎮 Gaming · ⏱ 5 min lectura</div>
  {article_html}
  <div class="disclaimer">
    ⚠️ Aviso de afiliados: Como Asociado de Amazon, obtenemos una pequeña comisión por compras realizadas a través de nuestros enlaces, sin coste adicional para ti. Esto nos ayuda a mantener el blog gratuito.
  </div>
</main>
<footer>{blog_data['blog_name']} © {datetime.now().year}</footer>
</body>
</html>"""

    # Publish article
    sha = github_get_file_sha(filename)
    github_put(filename, full_html, f"📝 Artículo: {keyword_data['article_title']}", sha)
    print(f"  ✓ Artículo publicado: {article_url}")

    # Update articles index
    index_path = "docs/articles/index.json"
    existing = github_get(index_path)
    if existing and "content" in existing:
        index_data = json.loads(base64.b64decode(existing["content"]).decode())
        index_sha = existing["sha"]
    else:
        index_data = {"articles": []}
        index_sha = None

    index_data["articles"].insert(0, {
        "title": keyword_data["article_title"],
        "keyword": keyword_data["keyword"],
        "url": article_url,
        "date": today,
        "excerpt": excerpt,
        "slug": slug
    })
    # Keep last 100 articles in index
    index_data["articles"] = index_data["articles"][:100]

    github_put(index_path, json.dumps(index_data, ensure_ascii=False, indent=2),
               f"📋 Index: +{slug}", index_sha)

    return article_url

def get_or_create_blog_config():
    """Obtiene o crea la config del blog (nombre, dominio, etc.)"""
    config_path = "agents/blog/config.json"
    existing = github_get(config_path)
    if existing and "content" in existing:
        config = json.loads(base64.b64decode(existing["content"]).decode())
        print(f"✓ Blog existente: {config['blog_name']}")
        return config, False  # (config, is_new)

    print("🆕 Primer run — eligiendo nombre del blog...")
    config = choose_blog_name()
    sha = github_get_file_sha(config_path)
    github_put(config_path, json.dumps(config, ensure_ascii=False, indent=2),
               "🎮 Blog config inicial", sha)
    print(f"✓ Blog creado: {config['blog_name']} ({config['domain']})")
    return config, True  # (config, is_new)

def save_pins_report(pins_data, article_url, keyword_data):
    """Guarda los pins en un archivo para revisión manual si Pinterest no está configurado."""
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = f"agents/blog/pins_pending/{today}.json"
    report = {
        "date": today,
        "article": keyword_data["article_title"],
        "article_url": article_url,
        "pins": pins_data.get("pins", [])
    }
    sha = github_get_file_sha(report_path)
    github_put(report_path, json.dumps(report, ensure_ascii=False, indent=2),
               f"📌 Pins: {keyword_data['keyword']}", sha)
    print(f"  ✓ {len(report['pins'])} pins guardados para Pinterest")

def main():
    print("🎮 Gaming Blog + Pinterest Agent iniciando...")
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Get or create blog config
    blog_data, is_new = get_or_create_blog_config()

    # 2. If new blog, create site structure
    if is_new:
        print("🏗 Creando estructura del blog...")
        ensure_site_structure(blog_data)

    # 3. Find keyword
    print("🔍 Buscando keyword SEO...")
    keyword_data = find_keyword()
    print(f"  ✓ Keyword: '{keyword_data['keyword']}' (~{keyword_data['monthly_searches']:,} búsquedas/mes)")

    # 4. Write article
    print("✍️ Escribiendo artículo SEO...")
    article_html = write_article(keyword_data, blog_data)
    print(f"  ✓ Artículo escrito ({len(article_html)} chars)")

    # 5. Publish to GitHub Pages
    print("📤 Publicando en GitHub Pages...")
    article_url = publish_article(article_html, keyword_data, blog_data)

    # 6. Generate Pinterest pins
    print("📌 Generando pins de Pinterest...")
    pins_data = generate_pins(keyword_data, article_url, blog_data)

    # 7. Publish pins or save for manual upload
    published = 0
    for pin in pins_data.get("pins", []):
        if publish_pin(pin, article_url):
            published += 1
            time.sleep(2)  # Pinterest rate limit

    if published > 0:
        print(f"  ✓ {published} pins publicados en Pinterest")
    else:
        save_pins_report(pins_data, article_url, keyword_data)

    print(f"\n✅ Completado para {today}:")
    print(f"   Blog: {blog_data['blog_name']} ({blog_data['domain']})")
    print(f"   Artículo: {keyword_data['article_title']}")
    print(f"   URL: {article_url}")
    print(f"   Pins: {len(pins_data.get('pins', []))} generados")

if __name__ == "__main__":
    main()
