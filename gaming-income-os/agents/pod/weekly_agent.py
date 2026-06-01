"""
Gaming POD Weekly Agent — Powered by Google Gemini (GRATIS)
Corre cada lunes via GitHub Actions:
1. Detecta top 3 tendencias gaming con búsqueda web
2. Genera 3 diseños por tendencia (9 total)
3. Genera imágenes con Ideogram API
4. Manda email con todo listo para subir a Redbubble
"""

import os, json, re, smtplib, requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

GEMINI_API  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
IDEOGRAM_API = "https://api.ideogram.ai/generate"

GEMINI_KEY   = os.environ["GEMINI_API_KEY"]
IDEOGRAM_KEY = os.environ["IDEOGRAM_API_KEY"]
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_APP_PASSWORD"]
EMAIL_TO     = os.environ["EMAIL_TO"]

def gemini(prompt):
    """Llama a Gemini 1.5 Flash y devuelve JSON parseado."""
    r = requests.post(
        f"{GEMINI_API}?key={GEMINI_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 1500
            }
        }
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)

def get_trends():
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Hoy es {today}. Eres experto en tendencias gaming y print-on-demand.
Basándote en tu conocimiento de los juegos más populares, tendencias virales de gaming,
juegos recientes con mucha comunidad, memes gaming y juegos con grandes comunidades en
Steam, Twitch y Reddit, identifica las 3 tendencias gaming MÁS relevantes ahora mismo.

Responde SOLO con JSON válido, sin markdown, sin backticks, sin texto adicional:
{{"trends":[{{"name":"nombre del juego o tendencia","reason":"por qué está popular ahora (max 6 palabras)","score":85}}]}}

Devuelve exactamente 3 tendencias ordenadas de mayor a menor score (60-99).
Ejemplos de buenas tendencias: juegos con DLC reciente, juegos virales en TikTok, remasters, temporadas nuevas."""
    return gemini(prompt)

def get_designs(trend):
    prompt = f"""Eres experto en print-on-demand para Redbubble y diseño gaming.
Genera diseños creativos y vendibles para la tendencia: "{trend['name']}"
Contexto: {trend['reason']}

Responde SOLO con JSON válido, sin markdown, sin backticks:
{{"designs":[
  {{
    "title": "nombre del diseño",
    "description": "descripción visual breve de 1-2 oraciones",
    "products": ["Camiseta", "Taza", "Sticker"],
    "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
    "imagePrompt": "very detailed english prompt for AI image generation, specific art style, colors, composition, suitable for t-shirt printing",
    "margin": 10
  }}
]}}

Genera exactamente 3 diseños con estilos variados:
1. Tipográfico (texto creativo con tipografía llamativa)
2. Ilustración detallada (personaje o escena del juego)
3. Pixel art / retro (estilo 8-bit o 16-bit)

Los prompts de imagen deben ser muy específicos en inglés, listos para Ideogram AI.
El margin es número entre 7 y 14."""
    return gemini(prompt)

def generate_image(prompt):
    try:
        r = requests.post(
            IDEOGRAM_API,
            headers={"Api-Key": IDEOGRAM_KEY, "Content-Type": "application/json"},
            json={
                "image_request": {
                    "prompt": prompt + ", transparent background, t-shirt design ready, high resolution, clean edges",
                    "aspect_ratio": "ASPECT_1_1",
                    "model": "V_2",
                    "magic_prompt_option": "AUTO"
                }
            }
        )
        r.raise_for_status()
        img_url = r.json()["data"][0]["url"]
        img_bytes = requests.get(img_url)
        img_bytes.raise_for_status()
        return img_bytes.content
    except Exception as e:
        print(f"  ⚠ Error generando imagen: {e}")
        return None

def build_email(all_results, date_str):
    total_designs = sum(len(r["designs"]) for r in all_results)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:-apple-system,sans-serif;background:#0a0a0f;color:#e2e2f0;margin:0;padding:0}}
.wrap{{max-width:680px;margin:0 auto;padding:28px 18px}}
.header{{text-align:center;padding:28px;background:linear-gradient(135deg,#0f0f1a,#12121a);border-radius:14px;margin-bottom:24px;border:1px solid #1e1e2e}}
.header h1{{margin:0 0 7px;font-size:1.7rem;background:linear-gradient(135deg,#e2e2f0,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{margin:0;color:#6b6b8a;font-size:0.85rem}}
.label{{color:#6b6b8a;font-size:0.68rem;font-family:monospace;letter-spacing:0.1em;margin-bottom:6px}}
.trend-block{{background:#12121a;border:1px solid #1e1e2e;border-radius:12px;padding:22px;margin-bottom:20px}}
.trend-name{{font-size:1.15rem;font-weight:700;color:#e2e2f0}}
.score{{background:rgba(0,255,136,0.12);border:1px solid rgba(0,255,136,0.3);color:#00ff88;padding:2px 9px;border-radius:16px;font-size:0.72rem;font-family:monospace;margin-left:8px}}
.card{{background:#0d0d18;border:1px solid #1e1e2e;border-radius:9px;padding:16px;margin:12px 0}}
.card-title{{font-size:0.95rem;font-weight:700;color:#e2e2f0;margin:0 0 6px}}
.desc{{color:#6b6b8a;font-size:0.8rem;line-height:1.5;margin:0 0 10px}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px}}
.tag{{background:rgba(0,255,136,0.08);border:1px solid rgba(0,255,136,0.22);color:#00ff88;padding:2px 8px;border-radius:14px;font-size:0.68rem;font-family:monospace}}
.prompt-box{{background:#070710;border:1px solid #1e1e2e;border-radius:7px;padding:11px;margin-bottom:10px}}
.prompt{{color:#c4c4e0;font-size:0.76rem;font-family:monospace;line-height:1.5}}
.products{{display:flex;flex-wrap:wrap;gap:5px}}
.product{{background:rgba(124,58,237,0.14);border:1px solid rgba(124,58,237,0.38);color:#a78bfa;padding:2px 9px;border-radius:5px;font-size:0.72rem}}
.margin{{background:rgba(0,255,136,0.1);border:1px solid #00ff88;color:#00ff88;padding:2px 9px;border-radius:5px;font-size:0.72rem;font-family:monospace;font-weight:700}}
.design-img{{width:100%;border-radius:7px;margin-bottom:10px;border:1px solid #1e1e2e}}
.steps{{background:#12121a;border:1px solid #1e1e2e;border-radius:12px;padding:22px;margin-top:6px}}
.step{{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid #1e1e2e;align-items:flex-start}}
.step:last-child{{border-bottom:none}}
.num{{background:rgba(0,255,136,0.14);color:#00ff88;min-width:25px;height:25px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:800}}
.step-text{{color:#6b6b8a;font-size:0.8rem;line-height:1.5;padding-top:3px}}
.footer{{text-align:center;margin-top:22px;color:#444;font-size:0.72rem}}
</style></head>
<body><div class="wrap">
<div class="header">
  <div style="font-size:0.68rem;font-family:monospace;color:#00ff88;letter-spacing:0.18em;margin-bottom:9px">▶ REPORTE SEMANAL AUTOMATIZADO</div>
  <h1>🎮 Gaming POD Agent</h1>
  <p>Semana del {date_str} — {total_designs} diseños listos para Redbubble</p>
</div>"""

    image_attachments = []
    img_counter = 0

    for tr in all_results:
        trend, designs, images = tr["trend"], tr["designs"], tr["images"]
        html += f"""
<div class="trend-block">
  <div style="display:flex;align-items:center;margin-bottom:6px">
    <span style="font-size:1.3rem;margin-right:8px">🔥</span>
    <span class="trend-name">{trend['name']}</span>
    <span class="score">Score {trend['score']}</span>
  </div>
  <p style="color:#6b6b8a;font-size:0.8rem;margin:0 0 16px">{trend['reason']}</p>"""

        for i, d in enumerate(designs):
            img_data = images[i] if i < len(images) else None
            cid = f"img_{img_counter}"; img_counter += 1
            html += f"""
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px">
      <div class="card-title">{d['title']}</div>
      <span class="margin">+${d['margin']}/venta</span>
    </div>
    <p class="desc">{d['description']}</p>"""
            if img_data:
                html += f'    <img class="design-img" src="cid:{cid}" alt="{d["title"]}">\n'
                image_attachments.append((cid, img_data))
            html += f"""    <div class="tags">{''.join(f'<span class="tag">#{t}</span>' for t in d['tags'])}</div>
    <div class="prompt-box">
      <div class="label">🖼️ PROMPT PARA IDEOGRAM / LEONARDO AI</div>
      <div class="prompt">{d['imagePrompt']}</div>
    </div>
    <div class="products">{''.join(f'<span class="product">{p}</span>' for p in d['products'])}</div>
  </div>"""
        html += "</div>"

    html += """
<div class="steps">
  <h3 style="color:#e2e2f0;margin:0 0 14px;font-size:0.92rem">🗺️ Cómo subir a Redbubble (15–20 min total)</h3>
  <div class="step"><div class="num">1</div><div class="step-text">Descarga las imágenes adjuntas en este email</div></div>
  <div class="step"><div class="num">2</div><div class="step-text">Ve a redbubble.com → Add New Work → sube cada imagen</div></div>
  <div class="step"><div class="num">3</div><div class="step-text">Copia el título y los tags de este email → pégalos en Redbubble</div></div>
  <div class="step"><div class="num">4</div><div class="step-text">Activa los productos recomendados, define tu margen → Publica</div></div>
  <div class="step"><div class="num">5</div><div class="step-text">El próximo lunes recibirás nuevos diseños automáticamente</div></div>
</div>
<div class="footer">Gaming POD Agent • Gemini 1.5 Flash + Ideogram • GitHub Actions</div>
</div></body></html>"""

    return html, image_attachments

def send_email(html_body, image_attachments, date_str):
    msg = MIMEMultipart("related")
    msg["Subject"] = f"🎮 Gaming POD — {len(image_attachments)} diseños listos ({date_str})"
    msg["From"]    = GMAIL_USER
    msg["To"]      = EMAIL_TO
    alt = MIMEMultipart("alternative")
    msg.attach(alt)
    alt.attach(MIMEText(html_body, "html"))
    for cid, img_data in image_attachments:
        img = MIMEImage(img_data)
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline")
        msg.attach(img)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASS)
        smtp.sendmail(GMAIL_USER, EMAIL_TO, msg.as_string())

def main():
    date_str = datetime.now().strftime("%d/%m/%Y")
    print("🔍 Detectando tendencias gaming con Gemini...")
    trends = get_trends().get("trends", [])
    print(f"✓ Tendencias: {[t['name'] for t in trends]}")

    all_results = []
    for trend in trends:
        print(f"\n🎨 Diseños para: {trend['name']}")
        designs = get_designs(trend).get("designs", [])
        images = []
        for i, d in enumerate(designs):
            print(f"  🖼 Imagen {i+1}/{len(designs)}: {d['title']}")
            images.append(generate_image(d["imagePrompt"]))
        all_results.append({"trend": trend, "designs": designs, "images": images})

    print("\n📧 Enviando email...")
    html, attachments = build_email(all_results, date_str)
    send_email(html, attachments, date_str)
    print(f"✅ Email enviado con {len(attachments)} imágenes.")

if __name__ == "__main__":
    main()
