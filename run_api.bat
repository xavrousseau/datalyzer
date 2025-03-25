@echo off
chcp 65001 >nul
setlocal

echo ===================================
echo 🔄 Nettoyage et redémarrage de Datalyzer
echo ===================================

:: 🔴 Fermeture des anciens processus Python et Uvicorn (si existants)
echo 🚫 Fermeture des anciens processus Python et Uvicorn...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
timeout /t 2 >nul 2>&1

:: 🔴 Suppression des caches Python (__pycache__ et .pyc)
echo 🗑️ Suppression des fichiers cache...
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /S /Q "%%d"
for /r %%f in (*.pyc) do @if exist "%%f" del "%%f" /F /Q

:: 🔴 Vérification de l'existence de l'environnement virtuel
if not exist .venv (
    echo ⚠️ Environnement virtuel non trouvé ! Création en cours...
    python -m venv .venv
)

:: 🔄 Activation de l'environnement virtuel
echo 🚀 Activation de l'environnement virtuel...
call .venv\Scripts\activate

:: 🔄 Vérification et mise à jour des dépendances
echo 🔄 Vérification des dépendances Python...
pip install --upgrade pip
pip install -r requirements.txt

:: 🔄 Nettoyage du cache pip
echo � Nettoyage du cache pip...
pip cache purge

:: 🔄 Définition du PYTHONPATH
echo 📌 Définition de PYTHONPATH...
set PYTHONPATH=F:\1.Boulot\03_Github\datalyzer

:: Pause pour éviter les conflits de démarrage
timeout /t 2 >nul 2>&1

:: 🔥 Lancement de l'API Datalyzer sur le port 8600
echo 🚀 Lancement de l'API Datalyzer sur http://127.0.0.1:8600...
start "" http://127.0.0.1:8600/docs
python -m uvicorn app.main:app --reload --port 8600 --log-level debug

:: Fin du script
endlocal