@echo off
cd ..

echo ========================================
echo 📜 LOGS DE L’APPLICATION DATALYZER (Streamlit)
echo ========================================
echo.

:: Nom du conteneur Docker (ajuste si besoin)
set CONTAINER_NAME=streamlit

:: Affiche les logs en direct (streaming)
echo 🔍 Suivi en temps réel du conteneur : %CONTAINER_NAME%
echo (Appuie sur CTRL+C pour quitter)
echo.

docker logs -f %CONTAINER_NAME%

pause
