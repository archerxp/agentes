"""
Gaming Twitter/X Agent — Powered by Google Gemini
Corre 3 veces al día: 9am, 3pm, 9pm UTC
Alterna formatos: curiosidad, hilo, pregunta
"""

import os, json, re, requests, base64, time
from datetime import datetime

GEMINI_KEY          = os.environ["GEMINI_API_KEY"]
TWITTER_KEY         = os.environ.get("TWITTER_API_KEY", "")
TWITTER_SECRET      = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_TOKEN       = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_TOKEN_SEC   = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
AMAZON_TAG          = os.environ.get("AMAZON_AFFILIATE_TAG", "gamingincome-20")
GITHUB_TOKEN        = os.environ["GITHUB_TOKEN"]
GITHUB_REPO         = os.environ["GITHUB_REPO"]
GITHUB_API          = f"https://api.github.com/repos/{GITHUB_REPO}"
GEMINI_API          = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def gemini_json(prompt):
    r = requests.post(f"{GEMINI_API}?key={GEMINI_KEY}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1000}})
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(re.sub(r"```json|```", "", text).strip())

def github_put(path, content, message):
    existing = requests.get(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = existing.json().get("sha") if existing.status_code == 200 else None
    body = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: body["sha"] = sha
    requests.put(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}"}, json=body)

def get_format():
    h = datetime.now().hour
    return "curiosidad" if h < 12 else ("hilo" if h < 18 else "pregunta")

def generate_post(fmt):
    today = datetime.now().strftime("%Y-%m-%d")
    return gemini_json(f"""Hoy es {today}. Gestor de redes gaming en X/Twitter. Formato: {fmt}

- curiosidad: dato gaming sorprendente (1 tweet máx 270 chars + emojis + hashtags)
- hilo: 4 tweets numerados sobre tema gaming (cada uno máx 270 chars)
- pregunta: pregunta que genere debate gaming (1 tweet máx 270 chars)

SOLO JSON sin markdown:
{{"format":"{fmt}","topic":"tema del post","posts":[{{"text":"texto tweet con emojis y hashtags","is_first":true}}]}}

Para hilo: 4 objetos en posts[].
Hashtags: #Gaming #Videojuegos #GamersLife #PCGaming
Tono: gamer apasionado, cercano, no corporativo.""")

def post_tweet(text):
    if not all([TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SEC]):
        return None
    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SEC)
        r = requests.post("https://api.twitter.com/2/tweets",
            auth=auth, json={"text": text[:280]})
        if r.status_code == 201:
            return r.json()["data"]["id"]
    except Exception as e:
        print(f"  ⚠ {e}")
    return None

def post_thread(posts):
    if not all([TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SEC]):
        return []
    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SEC)
        ids, reply_to = [], None
        for post in posts:
            body = {"text": post["text"][:280]}
            if reply_to: body["reply"] = {"in_reply_to_tweet_id": reply_to}
            r = requests.post("https://api.twitter.com/2/tweets", auth=auth, json=body)
            if r.status_code == 201:
                tid = r.json()["data"]["id"]
                ids.append(tid); reply_to = tid; time.sleep(1)
        return ids
    except Exception as e:
        print(f"  ⚠ {e}")
        return []

def save_report(post_data):
    today = datetime.now().strftime("%Y-%m-%d")
    hour  = datetime.now().strftime("%H%M")
    github_put(f"agents/twitter/pending/{today}_{hour}.json",
               json.dumps(post_data, ensure_ascii=False, indent=2),
               f"🐦 {post_data['topic'][:40]}")
    print("  ✓ Post guardado en agents/twitter/pending/")

def update_stats(post_data, n_published):
    path = "agents/twitter/stats.json"
    ex = requests.get(f"{GITHUB_API}/contents/{path}",
        headers={"Authorization": f"token {GITHUB_TOKEN}"})
    stats = json.loads(base64.b64decode(ex.json()["content"]).decode()) if ex.status_code == 200 else {"total_posts": 0, "total_published": 0, "history": []}
    stats["total_posts"] += len(post_data["posts"])
    stats["total_published"] += n_published
    stats["history"] = ([{"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "topic": post_data["topic"], "format": post_data["format"], "published": n_published > 0}] + stats.get("history", []))[:100]
    github_put(path, json.dumps(stats, ensure_ascii=False, indent=2), f"📊 +{len(post_data['posts'])} posts")

def main():
    print("🐦 Twitter/X Agent iniciando...")
    fmt = get_format()
    print(f"  Formato: {fmt}")

    print("📝 Generando post...")
    post_data = generate_post(fmt)
    print(f"  ✓ Tema: {post_data['topic']}")
    for p in post_data["posts"]:
        print(f"  → {p['text'][:80]}...")

    twitter_ok = all([TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TOKEN_SEC])
    published_ids = []

    if twitter_ok:
        print("📤 Publicando en X/Twitter...")
        if fmt == "hilo" and len(post_data["posts"]) > 1:
            published_ids = post_thread(post_data["posts"])
            print(f"  ✓ Hilo: {len(published_ids)} tweets")
        else:
            tid = post_tweet(post_data["posts"][0]["text"])
            if tid:
                published_ids = [tid]
                print(f"  ✓ Tweet publicado")
    else:
        save_report(post_data)

    update_stats(post_data, len(published_ids))
    print(f"\n✅ Completado | Publicados: {len(published_ids)}")

if __name__ == "__main__":
    main()
