@echo off
cd /d "%~dp0"

echo Installation de Texte vers Video
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Installe-le depuis https://www.python.org/downloads/
    echo IMPORTANT : coche "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)

where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffmpeg_ok

echo ffmpeg n'est pas dans le PATH. Recherche d'une installation existante...
set "FFMPEG_FOUND="
for /f "delims=" %%F in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ffmpeg.exe" 2^>nul') do set "FFMPEG_FOUND=%%F"
if defined FFMPEG_FOUND goto ffmpeg_found

echo Aucune installation existante trouvee, installation via winget...
where winget >nul 2>nul
if errorlevel 1 goto ffmpeg_no_winget

winget install --id=Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
echo Recherche du dossier d'installation...
for /f "delims=" %%F in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ffmpeg.exe" 2^>nul') do set "FFMPEG_FOUND=%%F"
if defined FFMPEG_FOUND goto ffmpeg_found

echo [ATTENTION] ffmpeg introuvable apres installation.
echo Installe-le manuellement si besoin : https://ffmpeg.org/download.html
goto ffmpeg_ok

:ffmpeg_found
for %%P in ("%FFMPEG_FOUND%") do set "FFMPEG_DIR=%%~dpP"
echo %FFMPEG_DIR%> ffmpeg_path.txt
set "PATH=%PATH%;%FFMPEG_DIR%"
echo ffmpeg trouve : %FFMPEG_DIR%
goto ffmpeg_ok

:ffmpeg_no_winget
echo [ATTENTION] winget est introuvable sur ce PC.
echo Installe ffmpeg manuellement : https://ffmpeg.org/download.html

:ffmpeg_ok
echo.

echo Creation de l'environnement virtuel...
python -m venv venv
if errorlevel 1 (
    echo [ERREUR] La creation de l'environnement virtuel a echoue.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel.
    pause
    exit /b 1
)

echo Installation des dependances (ca peut prendre 1-2 minutes)...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] L'installation des dependances Python a echoue. Voir le message ci-dessus.
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul
    echo.
    set /p PEXELS_KEY="Colle ta cle API Pexels (https://www.pexels.com/api/) : "
    powershell -Command "(Get-Content .env) -replace 'colle_ta_cle_ici', '%PEXELS_KEY%' | Set-Content .env"
    echo Cle enregistree dans .env
)

echo.
echo ============================================
echo Installation terminee !
echo Lance l'application avec : run.bat
echo ============================================
pause
exit /b 0
