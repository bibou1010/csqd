@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo [ERREUR] L'app n'est pas encore installee. Lance d'abord : install.bat
    pause
    exit /b 1
)

if exist "ffmpeg_path.txt" (
    for /f "delims=" %%P in (ffmpeg_path.txt) do set "PATH=%PATH%;%%P"
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel. Relance install.bat.
    pause
    exit /b 1
)

python app.py
if errorlevel 1 (
    echo.
    echo [ERREUR] L'application s'est arretee avec une erreur ^(voir ci-dessus^).
)

echo.
echo Fenetre a garder ouverte tant que tu utilises l'appli. Ferme-la pour arreter le serveur.
pause
