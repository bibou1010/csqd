"""
Interface web pour générer des vidéos à partir d'un texte, avec choix
manuel de l'image/vidéo de chaque scène (Pexels + Pixabay).
Lance ce fichier puis ouvre http://localhost:5000 dans ton navigateur.
"""
import os
import uuid
import threading
import webbrowser

from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect, url_for

import main as generator
import settings_store
from config import OUTPUT_DIR

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
APP_PASSWORD = os.getenv("APP_PASSWORD", "")  # si défini, protège l'app par mot de passe (usage hébergé)

JOBS = {}  # job_id -> {"status": "running"|"done"|"error", "log": [...], "output": str|None}

LOGIN_PAGE = """
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connexion</title>
<style>
body{margin:0;background:#f7f5f2;color:#1c1a17;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;}
form{background:#fff;padding:28px;border-radius:14px;border:1px solid #e6e0d7;width:280px;}
input{width:100%;padding:10px;border-radius:8px;border:1px solid #e6e0d7;font-size:0.95rem;margin-top:10px;box-sizing:border-box;}
button{width:100%;margin-top:14px;background:#b5502e;color:#fff;border:none;padding:10px;border-radius:999px;cursor:pointer;}
.err{color:#b5502e;font-size:0.85rem;margin-top:8px;}
</style></head><body>
<form method="POST">
  <div>🔒 Mot de passe</div>
  <input type="password" name="password" autofocus>
  {% if error %}<div class="err">Mot de passe incorrect.</div>{% endif %}
  <button type="submit">Entrer</button>
</form>
</body></html>
"""


@app.before_request
def require_login():
    if not APP_PASSWORD:
        return
    if request.endpoint in ("login", "static"):
        return
    if not session.get("authed"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["authed"] = True
            return redirect(url_for("index"))
        error = True
    return render_template_string(LOGIN_PAGE, error=error)


PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Texte → Vidéo</title>
<style>
  :root { --bg:#f7f5f2; --panel:#fff; --text:#1c1a17; --muted:#6b6357; --accent:#b5502e; --border:#e6e0d7; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
  .wrap { max-width: 820px; margin: 0 auto; padding: 32px 18px 60px; }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  p.sub { color: var(--muted); margin: 0 0 22px; font-size: 0.92rem; }
  .warn { background:#fdecea; border:1px solid #f3b9b0; color:#8a2d1f; padding:10px 14px; border-radius:10px; font-size:0.85rem; margin-bottom:18px; }
  textarea { width:100%; min-height:150px; padding:14px; border-radius:12px; border:1px solid var(--border); background:var(--panel); font-size:0.95rem; font-family:inherit; resize:vertical; }
  input[type=text], input[type=number] { width:100%; padding:10px 12px; border-radius:10px; border:1px solid var(--border); font-size:0.9rem; }
  .row { display:flex; gap:10px; align-items:center; margin-top:14px; flex-wrap:wrap; }
  label.field { flex:1; min-width:140px; font-size:0.82rem; color:var(--muted); }
  label.toggle { display:flex; align-items:center; gap:6px; font-size:0.85rem; color:var(--muted); }
  button { background:var(--accent); color:#fff; border:none; padding:11px 20px; border-radius:999px; font-size:0.92rem; cursor:pointer; }
  button.secondary { background:var(--panel); color:var(--accent); border:1px solid var(--accent); padding:6px 14px; font-size:0.8rem; }
  button:disabled { opacity:0.5; cursor:default; }
  .log { margin-top:22px; background:#141210; color:#d8d2c6; border-radius:12px; padding:14px; font-family:ui-monospace,monospace; font-size:0.82rem; white-space:pre-wrap; max-height:320px; overflow-y:auto; display:none; }
  .result { margin-top:18px; display:none; }
  .result a { display:inline-block; background:var(--accent); color:#fff; text-decoration:none; padding:10px 18px; border-radius:999px; font-size:0.9rem; }
  video.preview { width:100%; border-radius:12px; margin-top:12px; }
  .scenes { margin-top: 26px; display:none; flex-direction:column; gap:16px; }
  .scene { background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:14px; }
  .scene .num { font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.05em; }
  .scene .text { font-size:0.92rem; margin:4px 0 10px; line-height:1.4; }
  .thumbs { display:flex; gap:8px; flex-wrap:wrap; }
  .thumb { position:relative; width:84px; height:84px; border-radius:10px; overflow:hidden; cursor:pointer; border:3px solid transparent; background:#ddd; }
  .thumb img { width:100%; height:100%; object-fit:cover; display:block; }
  .thumb.selected { border-color:var(--accent); }
  .thumb .badge { position:absolute; bottom:2px; left:2px; background:rgba(0,0,0,0.6); color:#fff; font-size:0.6rem; padding:1px 5px; border-radius:6px; }
  .more-btn { width:84px; height:84px; border-radius:10px; border:2px dashed var(--border); background:none; color:var(--muted); font-size:0.75rem; cursor:pointer; }
  .empty { font-size:0.82rem; color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <h1>🎬 Texte → Vidéo</h1>
  <p class="sub">Colle ton récit, choisis l'image ou la vidéo de chaque scène parmi plusieurs propositions (Pexels{{ " + Pixabay" if has_pixabay else "" }}), puis génère la vidéo finale. — <a href="/settings" style="color:var(--accent);">⚙️ Réglages</a></p>
  {% if not has_key %}
  <div class="warn">⚠️ Aucune clé API détectée (PEXELS_API_KEY / PIXABAY_API_KEY). Ajoute-en au moins une dans .env puis relance l'app.</div>
  {% endif %}

  <textarea id="text" placeholder="Colle ton texte ici..."></textarea>

  <div class="row">
    <label class="field">Options par scène
      <input type="number" id="count" value="{{ default_count }}" min="2" max="10">
    </label>
    <label class="field">Nom du fichier de sortie
      <input type="text" id="output" value="video.mp4">
    </label>
    <label class="toggle"><input type="checkbox" id="tts"> Voix off automatique (TTS)</label>
  </div>

  <div class="row">
    <button id="split">Découper le texte et voir les options</button>
  </div>

  <div class="scenes" id="scenes"></div>

  <div class="row" id="generateRow" style="display:none;">
    <button id="go">Générer la vidéo finale</button>
  </div>

  <div class="log" id="log"></div>
  <div class="result" id="result">
    <video class="preview" id="preview" controls></video>
    <div style="margin-top:10px;"><a id="dl" href="#" download>Télécharger la vidéo</a></div>
  </div>
</div>

<script>
let SCENES = []; // [{text, query, candidates:[...], selectedIndex, page}]

function renderScenes() {
  const container = document.getElementById("scenes");
  container.style.display = "flex";
  container.innerHTML = "";
  SCENES.forEach((scene, sIdx) => {
    const div = document.createElement("div");
    div.className = "scene";
    const thumbsHtml = scene.candidates.map((c, cIdx) => `
      <div class="thumb ${cIdx === scene.selectedIndex ? 'selected' : ''}" data-scene="${sIdx}" data-cand="${cIdx}">
        <img src="${c.thumbnail}" loading="lazy">
        <span class="badge">${c.type === 'video' ? '🎬' : '🖼️'} ${c.source}</span>
      </div>`).join("");
    div.innerHTML = `
      <div class="num">Scène ${sIdx + 1} — mots-clés : "${scene.query}"</div>
      <div class="text">${scene.text.replace(/</g, "&lt;")}</div>
      <div class="thumbs">
        ${thumbsHtml || '<span class="empty">Aucun résultat pour cette recherche.</span>'}
        <button class="more-btn" data-scene="${sIdx}">+ Plus d'options</button>
      </div>`;
    container.appendChild(div);
  });

  container.querySelectorAll(".thumb").forEach(el => {
    el.addEventListener("click", () => {
      const sIdx = +el.dataset.scene, cIdx = +el.dataset.cand;
      SCENES[sIdx].selectedIndex = cIdx;
      renderScenes();
    });
  });
  container.querySelectorAll(".more-btn").forEach(el => {
    el.addEventListener("click", async () => {
      const sIdx = +el.dataset.scene;
      el.textContent = "...";
      const scene = SCENES[sIdx];
      scene.page = (scene.page || 1) + 1;
      const res = await fetch("/scenes/more", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: scene.query, page: scene.page, count: +document.getElementById("count").value })
      });
      const data = await res.json();
      scene.candidates = scene.candidates.concat(data.candidates || []);
      renderScenes();
    });
  });

  document.getElementById("generateRow").style.display = SCENES.length ? "flex" : "none";
}

document.getElementById("split").addEventListener("click", async () => {
  const text = document.getElementById("text").value.trim();
  if (!text) { alert("Colle d'abord un texte."); return; }
  const btn = document.getElementById("split");
  btn.disabled = true; btn.textContent = "Recherche en cours...";

  const res = await fetch("/scenes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, count: +document.getElementById("count").value })
  });
  const data = await res.json();
  SCENES = (data.scenes || []).map(s => ({ ...s, selectedIndex: 0, page: 1 }));
  renderScenes();

  btn.disabled = false; btn.textContent = "Découper le texte et voir les options";
});

const goBtn = document.getElementById("go");
const logBox = document.getElementById("log");
const result = document.getElementById("result");

async function poll(jobId) {
  const res = await fetch(`/status/${jobId}`);
  const data = await res.json();
  logBox.style.display = "block";
  logBox.textContent = data.log.join("\\n");
  logBox.scrollTop = logBox.scrollHeight;

  if (data.status === "running") {
    setTimeout(() => poll(jobId), 1500);
  } else {
    goBtn.disabled = false;
    goBtn.textContent = "Générer la vidéo finale";
    if (data.status === "done" && data.output) {
      result.style.display = "block";
      document.getElementById("preview").src = `/download/${data.output}`;
      document.getElementById("dl").href = `/download/${data.output}`;
    }
  }
}

goBtn.addEventListener("click", async () => {
  if (!SCENES.length) return;
  goBtn.disabled = true;
  goBtn.textContent = "Génération en cours...";
  result.style.display = "none";
  logBox.style.display = "block";
  logBox.textContent = "Démarrage...";

  const payload = {
    output: document.getElementById("output").value || "video.mp4",
    tts: document.getElementById("tts").checked,
    scenes: SCENES.map(s => ({ text: s.text, candidate: s.candidates[s.selectedIndex] || null }))
  };

  const res = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  poll(data.job_id);
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    s = settings_store.get()
    return render_template_string(
        PAGE,
        has_key=bool(s["pexels_api_key"] or s["pixabay_api_key"]),
        has_pixabay=bool(s["pixabay_api_key"]),
        default_count=s["candidates_per_scene"],
    )


SETTINGS_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Réglages</title>
<style>
  :root { --bg:#f7f5f2; --panel:#fff; --text:#1c1a17; --muted:#6b6357; --accent:#b5502e; --border:#e6e0d7; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
  .wrap { max-width: 560px; margin: 0 auto; padding: 32px 18px 60px; }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  a.back { color:var(--accent); font-size:0.85rem; text-decoration:none; }
  .ok { background:#e9f6ec; border:1px solid #b9e0c3; color:#1e5c31; padding:10px 14px; border-radius:10px; font-size:0.85rem; margin:16px 0; }
  fieldset { border:1px solid var(--border); border-radius:12px; padding:16px; margin-top:18px; }
  legend { font-size:0.85rem; font-weight:600; color:var(--muted); padding:0 6px; }
  label { display:block; font-size:0.82rem; color:var(--muted); margin-top:12px; }
  input[type=text], input[type=password], input[type=number], select {
    width:100%; padding:9px 11px; border-radius:8px; border:1px solid var(--border); font-size:0.9rem; margin-top:4px;
  }
  .hint { font-size:0.75rem; color:var(--muted); margin-top:3px; }
  .toggle-row { display:flex; align-items:center; gap:8px; margin-top:12px; }
  button { margin-top:22px; background:var(--accent); color:#fff; border:none; padding:11px 22px; border-radius:999px; font-size:0.92rem; cursor:pointer; }
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="/">← Retour</a>
  <h1>⚙️ Réglages</h1>
  {% if saved %}<div class="ok">Réglages enregistrés.</div>{% endif %}
  <form method="POST">
    <fieldset>
      <legend>Sources d'images/vidéos</legend>
      <label>Clé API Pexels
        <input type="password" name="pexels_api_key" value="{{ s.pexels_api_key }}" placeholder="pexels.com/api">
      </label>
      <label>Clé API Pixabay (optionnel)
        <input type="password" name="pixabay_api_key" value="{{ s.pixabay_api_key }}" placeholder="pixabay.com/api/docs">
      </label>
    </fieldset>

    <fieldset>
      <legend>Génération</legend>
      <label>Nombre d'options par scène (par défaut)
        <input type="number" name="candidates_per_scene" value="{{ s.candidates_per_scene }}" min="2" max="10">
      </label>
      <label>Format vidéo
        <select name="orientation">
          <option value="portrait" {{ "selected" if s.orientation == "portrait" }}>Portrait (réseaux sociaux, 1080x1920)</option>
          <option value="landscape" {{ "selected" if s.orientation == "landscape" }}>Paysage (YouTube, 1920x1080)</option>
        </select>
      </label>
      <label>Durée minimum par scène sans voix off (secondes)
        <input type="number" step="0.5" name="default_segment_duration" value="{{ s.default_segment_duration }}">
      </label>
      <div class="toggle-row">
        <input type="checkbox" id="enable_tts" name="enable_tts" {{ "checked" if s.enable_tts }}>
        <label for="enable_tts" style="margin:0;">Activer la voix off automatique par défaut</label>
      </div>
      <label>Langue de la voix off
        <input type="text" name="tts_lang" value="{{ s.tts_lang }}" placeholder="fr">
        <div class="hint">Code langue gTTS, ex. fr, en, es</div>
      </label>
    </fieldset>

    <fieldset>
      <legend>Audio</legend>
      <label>Volume de la musique de fond (0 à 1)
        <input type="number" step="0.05" min="0" max="1" name="music_volume" value="{{ s.music_volume }}">
      </label>
    </fieldset>

    <button type="submit">Enregistrer</button>
  </form>
</div>
</body>
</html>
"""


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    saved = False
    if request.method == "POST":
        settings_store.save({
            "pexels_api_key": request.form.get("pexels_api_key", "").strip(),
            "pixabay_api_key": request.form.get("pixabay_api_key", "").strip(),
            "candidates_per_scene": int(request.form.get("candidates_per_scene") or 4),
            "orientation": request.form.get("orientation", "portrait"),
            "default_segment_duration": float(request.form.get("default_segment_duration") or 4.5),
            "enable_tts": request.form.get("enable_tts") == "on",
            "tts_lang": request.form.get("tts_lang", "fr").strip() or "fr",
            "music_volume": float(request.form.get("music_volume") or 0.15),
        })
        saved = True
    return render_template_string(SETTINGS_PAGE, s=settings_store.get(), saved=saved)


@app.route("/scenes", methods=["POST"])
def scenes_route():
    data = request.get_json()
    text = data.get("text", "")
    count = int(data.get("count") or settings_store.get()["candidates_per_scene"])
    scenes = generator.build_scenes(text, candidates_per_scene=count)
    return jsonify({"scenes": scenes})


@app.route("/scenes/more", methods=["POST"])
def scenes_more_route():
    data = request.get_json()
    query = data.get("query", "")
    page = int(data.get("page") or 2)
    count = int(data.get("count") or settings_store.get()["candidates_per_scene"])
    candidates = generator.more_candidates(query, page=page, count=count)
    return jsonify({"candidates": candidates})


def _run_job(job_id, scenes, output_name, use_tts):
    def log(msg):
        JOBS[job_id]["log"].append(msg)

    try:
        output_path = generator.assemble_from_selection(scenes, output_name, enable_tts=use_tts, log=log)
        if output_path:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["output"] = os.path.basename(output_path)
        else:
            JOBS[job_id]["status"] = "error"
    except Exception as e:
        JOBS[job_id]["log"].append(f"❌ Erreur : {e}")
        JOBS[job_id]["status"] = "error"


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    scenes = data.get("scenes", [])
    output_name = data.get("output") or "video.mp4"
    if not output_name.endswith(".mp4"):
        output_name += ".mp4"
    use_tts = bool(data.get("tts", False))

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "log": [], "output": None}

    thread = threading.Thread(target=_run_job, args=(job_id, scenes, output_name, use_tts), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "log": ["Job introuvable"], "output": None}), 404
    return jsonify(job)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(os.path.abspath(OUTPUT_DIR), filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    is_local = "PORT" not in os.environ
    if is_local:
        url = f"http://127.0.0.1:{port}"
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
        print(f"\n🚀 Ouvre {url} dans ton navigateur (ouverture automatique dans 1s)\n")
    app.run(host="0.0.0.0", port=port, debug=False)
