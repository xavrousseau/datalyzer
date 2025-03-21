@echo off
setlocal

echo Activation de l'environnement virtuel...
call .venv\Scripts\activate

echo Environnement activé

echo Définition de PYTHONPATH...
set PYTHONPATH=F:\1.Boulot\03_Github\datalyzer

echo Lancement de l'API Datalyzer sur le port 8500...
start http://127.0.0.1:8500/docs
uvicorn app.main:app --reload --port 8500

endlocal
