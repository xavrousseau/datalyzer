@echo off
cd ..

echo ========================================
echo 📦 LANCEMENT DE L'APPLICATION EDA EXPLORER
echo ========================================
echo.

:: Étape 1 : Build + lancement de l'app avec docker-compose
echo 🚀 Démarrage des services avec Docker Compose...
docker-compose up --build -d
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors du démarrage des conteneurs.
    pause
    exit /b
)

:: Pause 5 secondes pour laisser le temps aux services de démarrer
echo 🕒 Attente du démarrage des conteneurs...
timeout /t 5 >nul

:: Étape 2 : Ouverture de l'interface Streamlit
echo 🌐 Ouverture de l'interface Streamlit...
start http://localhost:8501

echo ✅ Application lancée. Bon EDA !
pause
