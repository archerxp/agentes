# 🎮 Gaming Income OS

Sistema completo de ingresos pasivos para el nicho gaming.
Todo en un repositorio. Todo automatizado. Tú solo ~35 min/semana.

---

## 🤖 Los 4 agentes

| Agente | Archivo | Horario | Plataformas |
|--------|---------|---------|-------------|
| 🎨 Print-on-Demand | `agents/pod/weekly_agent.py` | Lunes 8am | Redbubble, Teepublic |
| 📝 Blog + Pinterest | `agents/blog/daily_agent.py` | Diario 9am | GitHub Pages + Pinterest |
| 🎬 YouTube | `agents/youtube/weekly_agent.py` | Mié + Sáb 11am | YouTube + Shorts |
| 🐦 Twitter/X | `agents/twitter/daily_agent.py` | 9am, 3pm, 9pm | Twitter/X |

---

## ⚙️ Setup completo (~45 min, una sola vez)

### Paso 1 — Sube este repo a GitHub
- github.com → New repository → `gaming-income-os` (privado)
- Sube todos los archivos

### Paso 2 — Activa GitHub Pages (para el blog)
- Settings → Pages → Branch: main → Folder: /docs → Guardar

### Paso 3 — Configura los Secrets
Settings → Secrets and variables → Actions → New repository secret

#### 🟢 Obligatorios (arrancan POD + Blog)
| Secret | Cómo obtenerlo | Coste |
|--------|---------------|-------|
| `GEMINI_API_KEY` | aistudio.google.com → Get API Key | **Gratis** |
| `IDEOGRAM_API_KEY` | ideogram.ai → Settings → API | ~$0.18/sem |
| `GMAIL_USER` | tu@gmail.com | **Gratis** |
| `GMAIL_APP_PASSWORD` | myaccount.google.com → Seguridad → Contraseñas de apps | **Gratis** |
| `EMAIL_TO` | tu email de destino | **Gratis** |

#### 🟡 Añadir cuando estés listo (semana 2-3)
| Secret | Cómo obtenerlo |
|--------|---------------|
| `PINTEREST_TOKEN` | developers.pinterest.com → App → Access Token |
| `AMAZON_AFFILIATE_TAG` | affiliate-program.amazon.com → tu tag (ej: gaming-21) |
| `YOUTUBE_ACCESS_TOKEN` | console.cloud.google.com → YouTube Data API v3 |
| `ELEVENLABS_API_KEY` | elevenlabs.io → Profile → API Key (plan gratis: 10k chars/mes) |
| `TWITTER_API_KEY` | developer.twitter.com → App → Keys (plan gratuito disponible) |
| `TWITTER_API_SECRET` | developer.twitter.com |
| `TWITTER_ACCESS_TOKEN` | developer.twitter.com |
| `TWITTER_ACCESS_TOKEN_SECRET` | developer.twitter.com |

### Paso 4 — Activa GitHub Actions
- Pestaña Actions → "I understand my workflows, enable them"

### Paso 5 — Primer test
- Actions → "Blog + Pinterest Agent" → Run workflow
- En ~3 min tienes tu primer artículo publicado y el nombre del blog elegido

---

## 📅 Tu rutina semanal (~35 min)

**Cada lunes recibes un email con:**
- 9 diseños POD generados → tú los subes a Redbubble (20 min)
- Resumen de artículos publicados
- Videos generados para revisar y subir si YouTube no está configurado

**El resto lo hacen los agentes solos:**
- Blog: 1 artículo SEO nuevo cada día
- Twitter/X: 3 posts diarios (curiosidad, hilo, pregunta)
- YouTube: 2 videos por semana
- Pinterest: 5 pins por artículo publicado

---

## 💰 Costes semanales

| Concepto | Coste |
|----------|-------|
| Google Gemini | **Gratis** |
| GitHub Actions | **Gratis** |
| GitHub Pages | **Gratis** |
| Gmail | **Gratis** |
| gTTS (voz YouTube) | **Gratis** |
| Twitter API free tier | **Gratis** |
| Ideogram (9 imgs POD) | ~$0.18 |
| **Total** | **~$0.18/semana** |

Opcionales que mejoran calidad:
- ElevenLabs voz: $5/mes (voz mucho más natural en YouTube)
- Dominio propio blog: $10/año

---

## 🔄 Comportamiento sin API configurada

Cada agente funciona aunque falten APIs opcionales:
- **Sin Pinterest token** → guarda los pins en `agents/blog/pins_pending/` para subida manual
- **Sin YouTube token** → guarda el script y reporte en `agents/youtube/pending/` para subida manual
- **Sin Twitter tokens** → guarda los posts en `agents/twitter/pending/` para publicación manual
- **Sin Amazon tag** → usa tag genérico de ejemplo

---

## 📈 Proyección nicho gaming

| Mes | POD | Blog | Social | Total |
|-----|-----|------|--------|-------|
| 1 | $20 | $0 | $5 | $25 |
| 3 | $130 | $50 | $60 | $240 |
| 6 | $400 | $200 | $200 | $800 |
| 12 | $900 | $600 | $500 | $2,000 |

---

## 🔄 Duplicar para otro nicho

Cuando gaming sea estable (~mes 6):
1. Crea repo nuevo: `mascotas-income-os`
2. Copia todos estos archivos
3. Busca y reemplaza "gaming" por tu nuevo nicho en los prompts
4. Nuevas cuentas en cada plataforma
5. Nuevos secrets en el nuevo repo
6. Activa Actions → listo

---

## ❓ Preguntas frecuentes

**¿El agente de blog elige el nombre del blog solo?**
Sí. El primer run elige automáticamente el mejor nombre basado en SEO y lo guarda en `agents/blog/config.json`. Todos los runs siguientes usan ese nombre.

**¿Qué pasa si un agente falla?**
GitHub Actions te manda un email automático. Puedes ver el error en la pestaña Actions.

**¿Puedo pausar un agente?**
Sí. Actions → el workflow → Disable workflow.

**¿El blog necesita dominio propio?**
No. GitHub Pages funciona en `tuusuario.github.io/gaming-income-os`. Añade dominio cuando genere ingresos (~$10/año en Namecheap).

**¿Los videos de YouTube son buenos sin cara?**
Sí. El formato de narración + gameplay funciona muy bien en YouTube gaming. Canales como esta generan millones de vistas sin aparecer en cámara.
