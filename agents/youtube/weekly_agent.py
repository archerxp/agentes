"""
Gaming YouTube Agent — Powered by Google Gemini + gTTS/ElevenLabs
Corre 2 veces por semana via GitHub Actions:
1. Detecta tema viral gaming con alto potencial
2. Escribe script completo del video
3. Genera narración con voz sintética
4. Monta el video con subtítulos animados
5. Sube a YouTube automáticamente (o guarda reporte para subida manual)
"""

import os, json, re, time, requests, tempfile, subprocess, base64
from datetime import datetime

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()[:56]
YOUTUBE_TOKEN  = os.environ.get("YOUTUBE_ACCESS_TOKEN", "")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
AMAZON_TAG     = os.environ.get("AMAZON_AFFILIATE_TAG", "gamingincome-20")
GITHUB_TOKEN   = os.environ["GITHUB_TOKEN"]
GITHUB_REPO    = os.environ["GITHUB_REPO"]
GITHUB_API     = f"https://api.github.com/repos/{GITHUB_REPO}"
GEMINI_API     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def gemini(prompt, temperature=0.8):
    r = requests.post(GROQ_API,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {GROQ_KEY}"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": temperature, "max_tokens": 2000})
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"```json|```", "", text).strip()

def gemini_json(prompt): return json.loads(gemini(prompt))

def github_put(path, content, message):
    existing = requests.get(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = existing.json().get("sha") if existing.status_code == 200 else None
    body = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: body["sha"] = sha
    requests.put(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}"}, json=body)

def find_topic():
    today = datetime.now().strftime("%Y-%m-%d")
    return gemini_json(f"""Hoy es {today}. Experto en YouTube gaming. Encuentra el MEJOR tema para
un video gaming sin cara (narración + gameplay) que pueda viralizarse ahora.

Formatos que funcionan: Top 10, historia de un juego, secretos, comparativa, juegos infravalorados.

Responde SOLO JSON sin markdown:
{{"title":"título gancho (máx 70 chars)","topic":"descripción del tema","format":"top10|historia|comparativa|secretos","hook":"primera frase gancho del video","duration_mins":10,"affiliate_angle":"qué productos recomendar","tags":["t1","t2","t3","t4","t5","t6","t7","t8","t9","t10"],"description_seo":"descripción YouTube SEO (máx 300 chars)","thumbnail_prompt":"english prompt for YouTube gaming thumbnail, dramatic, high contrast, click-bait"}}""")

def write_script(topic):
    return gemini_json(f"""Escribe script completo de video YouTube gaming sin cara.
Título: {topic['title']} | Duración: {topic['duration_mins']} min | Afiliados: {topic['affiliate_angle']}

Responde SOLO JSON sin markdown:
{{"intro":"texto introducción 30 seg con gancho","sections":[{{"title":"título sección","narration":"texto narrar (150-200 palabras)","visual_notes":"qué mostrar en pantalla","duration_secs":90}}],"affiliate_mention":"texto natural mencionando productos con link https://amazon.es/s?k=PRODUCTO&tag={AMAZON_TAG}","outro":"cierre con call to action","full_narration":"texto completo concatenado para text-to-speech"}}

5-7 secciones. Tono entretenido y energético. Usa frases gancho: 'pero espera...', 'lo que nadie sabe...'""")

def generate_voice(text, output_path):
    if ELEVENLABS_KEY:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={"text": text[:3000], "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}})
        if r.status_code == 200:
            with open(output_path, "wb") as f: f.write(r.content)
            print(f"  ✓ Voz ElevenLabs ({len(r.content)//1024}KB)")
            return True
    # Fallback: gTTS (gratis)
    subprocess.run(["pip", "install", "gtts", "-q"], capture_output=True)
    from gtts import gTTS
    gTTS(text=text[:3000], lang="es").save(output_path)
    print("  ✓ Voz gTTS (gratis)")
    return True

def create_video(script, topic, audio_path, output_path):
    try:
        subprocess.run(["pip", "install", "moviepy==1.0.3", "Pillow", "-q"], capture_output=True)
        from moviepy.editor import AudioFileClip, TextClip, CompositeVideoClip, ColorClip

        audio = AudioFileClip(audio_path)
        duration = audio.duration
        bg = ColorClip(size=(1280, 720), color=(10, 10, 20), duration=duration)

        title_clip = (TextClip(topic["title"][:55], fontsize=48, color="white",
                               font="DejaVu-Sans-Bold", size=(1100, None), method="caption")
                      .set_position("center").set_duration(min(4, duration)))

        narration = script.get("full_narration", "")
        words = narration.split()
        wps = max(1, len(words) / duration)
        chunk_size = int(wps * 5)
        clips = [bg, title_clip]
        t = 0
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunk_dur = min(5, duration - t)
            if chunk_dur <= 0: break
            sub = (TextClip(chunk, fontsize=28, color="#00ff88", font="DejaVu-Sans",
                            size=(1100, None), method="caption", bg_color="rgba(0,0,0,0.75)")
                   .set_position(("center", 590)).set_start(t).set_duration(chunk_dur))
            clips.append(sub)
            t += chunk_dur

        CompositeVideoClip(clips).set_audio(audio).write_videofile(
            output_path, fps=24, codec="libx264", audio_codec="aac",
            verbose=False, logger=None)
        print(f"  ✓ Video montado")
        return True
    except Exception as e:
        print(f"  ⚠ Error video: {e}")
        return False

def upload_youtube(video_path, topic):
    if not YOUTUBE_TOKEN: return None
    meta = {"snippet": {"title": topic["title"], "description": f"{topic['description_seo']}\n\n#gaming {' '.join('#'+t for t in topic['tags'][:5])}", "tags": topic["tags"], "categoryId": "20"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    with open(video_path, "rb") as f: video_data = f.read()
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=multipart",
        headers={"Authorization": f"Bearer {YOUTUBE_TOKEN}"},
        files={"metadata": ("m.json", json.dumps(meta), "application/json"), "video": ("v.mp4", video_data, "video/mp4")})
    if r.status_code in [200, 201]:
        vid = r.json().get("id")
        print(f"  ✓ YouTube: https://youtube.com/watch?v={vid}")
        return f"https://youtube.com/watch?v={vid}"
    return None

def save_report(topic, script):
    today = datetime.now().strftime("%Y-%m-%d")
    report = {"date": today, "title": topic["title"], "description": topic["description_seo"],
              "tags": topic["tags"], "thumbnail_prompt": topic["thumbnail_prompt"],
              "affiliate_mention": script.get("affiliate_mention", ""),
              "full_script": script.get("full_narration", "")[:500] + "...",
              "steps": ["1. Genera miniatura en ideogram.ai con el thumbnail_prompt", "2. Ve a studio.youtube.com → Subir video", "3. Usa título, descripción y tags de este reporte"]}
    github_put(f"agents/youtube/pending/{today}.json",
               json.dumps(report, ensure_ascii=False, indent=2), f"🎬 {topic['title'][:40]}")
    print(f"  ✓ Reporte guardado para subida manual en agents/youtube/pending/")

def main():
    print("🎬 YouTube Agent iniciando...")
    today = datetime.now().strftime("%Y-%m-%d")

    print("🔍 Buscando tema viral...")
    topic = find_topic()
    print(f"  ✓ {topic['title']}")

    print("✍️ Escribiendo script...")
    script = write_script(topic)
    print(f"  ✓ {len(script.get('full_narration','').split())} palabras")

    with tempfile.TemporaryDirectory() as tmp:
        audio = os.path.join(tmp, "audio.mp3")
        video = os.path.join(tmp, "video.mp4")

        print("🎙️ Generando voz...")
        generate_voice(script.get("full_narration", ""), audio)

        print("🎬 Montando video...")
        video_ok = create_video(script, topic, audio, video)

        if video_ok:
            print("📤 Subiendo a YouTube...")
            url = upload_youtube(video, topic)
            if not url:
                save_report(topic, script)
        else:
            save_report(topic, script)

    print(f"\n✅ YouTube Agent completado: {topic['title']}")

if __name__ == "__main__":
    main()
