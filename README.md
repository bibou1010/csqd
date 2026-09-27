# Texte → Vidéo (images/vidéos libres de droit)

Génère automatiquement une vidéo à partir d'un texte : le script découpe le
récit en scènes, cherche sur **Pexels et Pixabay** (gratuits) des images ou
vidéos correspondant à chaque scène, te laisse **choisir ou changer**
l'image/vidéo de chaque scène parmi plusieurs propositions, puis assemble
le tout avec une musique de fond et, en option, une voix off synthétique.

Une page **⚙️ Réglages** (lien en haut de l'app) permet de changer les clés
API, le nombre d'options par scène, le format vidéo, la voix off et le
volume de la musique directement depuis le navigateur, sans toucher au code.

## ☁️ Héberger en ligne (accessible depuis n'importe où, sans installation locale)

Gratuit via **Render**, sans ligne de commande — tout se fait sur des sites web.

1. **Crée un compte GitHub** (gratuit) sur github.com si tu n'en as pas.
2. Sur GitHub, clique **New repository**, donne-lui un nom (ex. `text2video`),
   laisse-le en **Private**, clique **Create repository**.
3. Sur la page du repo vide, clique **uploading an existing file**, puis
   glisse-dépose **tous les fichiers de ce dossier** (pas le zip, les fichiers
   à l'intérieur) et clique **Commit changes**.
4. Crée un compte gratuit sur **render.com**, connecte-le à ton compte GitHub.
5. Clique **New +** → **Web Service**, choisis ton repo `text2video`.
6. Render détecte automatiquement le `Dockerfile`. Dans les réglages :
   - **Instance Type** : Free
   - Dans **Environment Variables**, ajoute :
     - `PEXELS_API_KEY` = ta clé Pexels
     - `PIXABAY_API_KEY` = ta clé Pixabay (optionnel, plus de choix par scène)
     - `APP_PASSWORD` = un mot de passe de ton choix (**important**, sinon
       n'importe qui trouvant l'URL peut utiliser ton app et tes clés)
7. Clique **Create Web Service**. Le premier build prend 3-5 minutes.
8. Une fois prêt, Render te donne une URL du type `https://text2video-xxxx.onrender.com`
   — ouvre-la, entre ton mot de passe, et c'est en ligne.

⚠️ Sur le plan gratuit, le service se met en veille après 15 min d'inactivité
(la première requête après la veille prend ~30s à réveiller le service) et le
stockage n'est pas garanti entre deux redémarrages : télécharge chaque vidéo
tout de suite après génération plutôt que de compter dessus pour la retrouver
plus tard. Pour la même raison, préfère définir tes clés API et réglages
comme variables d'environnement Render (persistantes) plutôt que via la page
⚙️ Réglages une fois hébergé (celle-ci est surtout utile en local, où elle
survit aux redémarrages).

---

## 💻 Installation locale (alternative — pas besoin de compte, aucune limite)

## 🚀 Installation clé en main (recommandé)

Tu n'as que 3 choses à faire :

1. Lance le script d'installation :
   - macOS/Linux : ouvre un terminal dans le dossier et tape `chmod +x install.sh run.sh && ./install.sh`
   - Windows : double-clique sur `install.bat`
   - (il installe ffmpeg automatiquement — sur Mac il peut te demander ton mot de passe admin, c'est normal)
2. Crée un compte gratuit sur [pexels.com/api](https://www.pexels.com/api/) et colle ta clé quand le script la demande. (Optionnel : ajoute aussi une clé [Pixabay](https://pixabay.com/api/docs/) dans `.env` en `PIXABAY_API_KEY=` pour plus de choix par scène.)
3. Lance l'appli : `./run.sh` ou double-clic sur `run.bat`. Le navigateur s'ouvre tout seul.

C'est tout — ffmpeg, l'environnement Python et les dépendances s'installent sans autre intervention.

---

## Installation manuelle (si tu préfères)

## 1. Prérequis

- Python 3.9+
- **ffmpeg** installé sur ta machine :
  - macOS : `brew install ffmpeg`
  - Windows : télécharge un build sur ffmpeg.org et ajoute-le au PATH
  - Linux : `sudo apt install ffmpeg`

## 2. Installation

```bash
cd text2video
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Clé API Pexels (gratuite)

1. Crée un compte sur https://www.pexels.com/api/
2. Récupère ta clé API
3. Copie `.env.example` en `.env` et colle ta clé :

```bash
cp .env.example .env
```

```
PEXELS_API_KEY=ta_cle_ici
```

## 4. Musique de fond (optionnel mais recommandé)

Dépose des fichiers `.mp3` ou `.wav` libres de droit dans `assets/music/`.
Le script en choisit un au hasard et le mixe en fond sonore.

Sources gratuites recommandées :
- Pixabay Music : https://pixabay.com/music/
- YouTube Audio Library
- Free Music Archive

## 5. Bruitages (optionnel)

Le dossier `assets/sfx/` est prévu pour tes propres effets sonores
(à intégrer manuellement pour l'instant — l'ajout automatique par scène
est une extension possible, voir "Pour aller plus loin").

## 6. Utilisation

```bash
# Texte direct
python main.py --text "Il était une fois, dans une forêt paisible..." --output histoire.mp4

# Depuis un fichier texte
python main.py --file mon_recit.txt --output histoire.mp4
```

La vidéo finale est générée dans `assets/output/`.

## 7. Activer la voix off automatique

Dans `.env`, mets :
```
ENABLE_TTS=true
TTS_LANG=fr
```
Utilise gTTS (Google Text-to-Speech), gratuit mais nécessite une connexion
internet au moment de la génération.

## Pour aller plus loin

- Remplacer l'extraction de mots-clés basique par un vrai NLP (spaCy) pour
  un ciblage plus fin des images/vidéos.
- Ajouter automatiquement un bruitage par scène selon un mapping mots-clés → sfx.
- Ajouter des sous-titres incrustés (moviepy `TextClip`, nécessite ImageMagick).
- Passer en format paysage (1920x1080) en changeant `VIDEO_WIDTH`/`VIDEO_HEIGHT`
  dans `config.py`.
