@echo off
setlocal

echo ----------------------------------------
echo Suppression de l'ancien environnement
echo ----------------------------------------
if exist .venv (
    rmdir /s /q .venv
    echo Ancien environnement supprimé
) else (
    echo  Aucun environnement à supprimer
)

echo ----------------------------------------
echo Création du nouvel environnement
echo ----------------------------------------
python -m venv .venv

if errorlevel 1 (
    echo Échec de la création de l'environnement virtuel
    exit /b 1
)

echo ----------------------------------------
echo Environnement virtuel créé
echo ----------------------------------------

echo ----------------------------------------
echo Installation des dépendances
echo ----------------------------------------

call .venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Échec lors de l'installation des dépendances
    exit /b 1
)

echo ----------------------------------------
echo Installation terminée
echo ----------------------------------------

echo Tu peux maintenant exécuter :
echo  python -m uvicorn app.main:app
echo ----------------------------------------

endlocal
pause
