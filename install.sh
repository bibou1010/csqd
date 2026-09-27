#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "🔧 Installation de Texte → Vidéo"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Installe-le d'abord : https://www.python.org/downloads/"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "🎞️  ffmpeg n'est pas détecté, tentative d'installation automatique..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            echo "   Homebrew n'est pas installé, installation..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
        fi
        brew install ffmpeg
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    else
        echo "   ⚠️  Impossible d'installer ffmpeg automatiquement sur ce système."
        echo "   Installe-le manuellement : https://ffmpeg.org/download.html"
    fi
    echo ""
fi

echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installation des dépendances..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "📝 Fichier .env créé à partir de .env.example."
    read -p "Colle ta clé API Pexels (https://www.pexels.com/api/) : " PEXELS_KEY
    if [ -n "$PEXELS_KEY" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/colle_ta_cle_ici/$PEXELS_KEY/" .env
        else
            sed -i "s/colle_ta_cle_ici/$PEXELS_KEY/" .env
        fi
        echo "✅ Clé enregistrée dans .env"
    else
        echo "⚠️  Aucune clé saisie, tu pourras l'ajouter plus tard dans .env"
    fi
fi

echo ""
echo "✅ Installation terminée !"
echo "👉 Lance l'application avec : ./run.sh"
