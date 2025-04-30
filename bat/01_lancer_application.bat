@echo off
REM ==========================================
REM SCRIPT : Lancer l'application EDA Explorer (Datalyzer)
REM Emplacement : bat/01_lancer_application.bat
REM Objectif : Build + run l'application via docker-compose, puis ouvrir Streamlit
REM ==========================================

REM Étape 0 : Remonter à la racine du projet (depuis /bat)
cd ..

echo ========================================
echo 📦 LANCEMENT DE L'APPLICATION EDA EXPLORER
echo ========================================
echo.

REM Étape 1 : Lancer docker-compose en mode détaché avec build
echo 🚀 Démarrage des services avec Docker Compose...
docker-compose up --build -d
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors du démarrage des conteneurs.
    pause
    exit /b
)

REM Étape 2 : Attendre quelques secondes pour que les services démarrent
echo 🕒 Attente du démarrage des conteneurs...
timeout /t 5 >nul

REM Étape 3 : Ouvrir l'application dans le navigateur
echo 🌐 Ouverture de l'interface Streamlit...
start http://localhost:8501

echo ✅ Application lancée avec succès. Bon EDA !
pause
