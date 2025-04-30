@echo off
cd ..

echo ========================================
echo 📊 STATUT DE L’APPLICATION DATALYZER
echo ========================================
echo.

:: Affiche uniquement les conteneurs liés à ce projet
echo 🔍 Conteneurs Docker actifs liés à Datalyzer :
docker ps --filter "name=streamlit" --format "  ▸ {{.Names}} – {{.Status}}"

:: Vérifie si aucun conteneur ne tourne
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Aucun conteneur actif trouvé pour ce projet.
) else (
    echo ✅ Conteneur(s) actif(s) détecté(s).
)

pause
