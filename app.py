"""
Interface web locale pour générer des vidéos à partir d'un texte.
Lance ce fichier puis ouvre http://localhost:5000 dans ton navigateur.
Tout tourne en local sur ta machine (aucune donnée envoyée ailleurs
qu'à l'API Pexels pour chercher les images/vidéos).
"""
import os
import uuid
import threading
import webbrowser

from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect, url_for

import main as generator
from config import OUTPUT_DIR, PEXELS_API_KEY

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
        return  # pas de mot de passe configuré = pas de protection (usage local)
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
  .wrap { max-width: 680px; margin: 0 auto; padding: 32px 18px 60px; }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  p.sub { color: var(--muted); margin: 0 0 22px; font-size: 0.92rem; }
  .warn { background:#fdecea; border:1px solid #f3b9b0; color:#8a2d1f; padding:10px 14px; border-radius:10px; font-size:0.85rem; margin-bottom:18px; }
  textarea { width:100%; min-height:150px; padding:14px; border-radius:12px; border:1px solid var(--border); background:var(--panel); font-size:0.95rem; font-family:inherit; resize:vertical; }
  input[type=text] { width:100%; padding:10px 12px; border-radius:10px; border:1px solid var(--border); font-size:0.9rem; }
  .row { display:flex; gap:10px; align-items:center; margin-top:14px; flex-wrap:wrap; }
  label.field { flex:1; min-width:160px; font-size:0.82rem; color:var(--muted); }
  label.toggle { display:flex; align-items:center; gap:6px; font-size:0.85rem; color:var(--muted); }
  button { background:var(--accent); color:#fff; border:none; padding:11px 20px; border-radius:999px; font-size:0.92rem; cursor:pointer; }
  button:disabled { opacity:0.5; cursor:default; }
  .log { margin-top:22px; background:#141210; color:#d8d2c6; border-radius:12px; padding:14px; font-family:ui-monospace,monospace; font-size:0.82rem; white-space:pre-wrap; max-height:320px; overflow-y:auto; display:none; }
  .result { margin-top:18px; display:none; }
  .result a { display:inline-block; background:var(--accent); color:#fff; text-decoration:none; padding:10px 18px; border-radius:999px; font-size:0.9rem; }
  video { width:100%; border-radius:12px; margin-top:12px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🎬 Texte → Vidéo</h1>
  <p class="sub">Colle ton récit, l'app cherche des images/vidéos libres de droit sur Pexels et monte la vidéo automatiquement.</p>
  {% if not has_key %}
  <div class="warn">⚠️ Aucune clé PEXELS_API_KEY détectée dans le fichier .env. Ajoute-la puis relance l'app.</div>
  {% endif %}

  <textarea id="text" placeholder="Colle ton texte ici..."></textarea>

  <div class="row">
    <label class="field">Nom du fichier de sortie
      <input type="text" id="output" value="video.mp4">
    </label>
    <label class="toggle"><input type="checkbox" id="tts"> Voix off automatique (TTS)</label>
  </div>

  <div class="row">
    <button id="go">Générer la vidéo</button>
  </div>

  <div class="log" id="log"></div>
  <div class="result" id="result">
    <video id="preview" controls></video>
    <div style="margin-top:10px;"><a id="dl" href="#" download>Télécharger la vidéo</a></div>
  </div>
</div>

<script>
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
    goBtn.textContent = "Générer la vidéo";
    if (data.status === "done" && data.output) {
      result.style.display = "block";
      document.getElementById("preview").src = `/download/${data.output}`;
      document.getElementById("dl").href = `/download/${data.output}`;
    }
  }
}

goBtn.addEventListener("click", async () => {
  const text = document.getElementById("text").value.trim();
  if (!text) { alert("Colle d'abord un texte."); return; }

  goBtn.disabled = true;
  goBtn.textContent = "Génération en cours...";
  result.style.display = "none";
  logBox.style.display = "block";
  logBox.textContent = "Démarrage...";

  const res = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      output: document.getElementById("output").value || "video.mp4",
      tts: document.getElementById("tts").checked
    })
  });
  const data = await res.json();
  poll(data.job_id);
});
</script>
</body>
</html>
"""


def _run_job(job_id, text, output_name, use_tts):
    def log(msg):
        JOBS[job_id]["log"].append(msg)

    try:
        output_path = generator.run(text, output_name, enable_tts=use_tts, log=log)
        if output_path:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["output"] = os.path.basename(output_path)
        else:
            JOBS[job_id]["status"] = "error"
    except Exception as e:
        JOBS[job_id]["log"].append(f"❌ Erreur : {e}")
        JOBS[job_id]["status"] = "error"


@app.route("/")
def index():
    return render_template_string(PAGE, has_key=bool(PEXELS_API_KEY))


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    text = data.get("text", "")
    output_name = data.get("output") or "video.mp4"
    if not output_name.endswith(".mp4"):
        output_name += ".mp4"
    use_tts = bool(data.get("tts", False))

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "log": [], "output": None}

    thread = threading.Thread(target=_run_job, args=(job_id, text, output_name, use_tts), daemon=True)
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
