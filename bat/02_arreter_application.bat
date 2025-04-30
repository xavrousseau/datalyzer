@echo off
cd ..

echo ========================================
echo 🛑 ARRÊT DE L’APPLICATION DATALYZER
echo ========================================
echo.

:: Arrêt des conteneurs via docker-compose
docker-compose down

IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Une erreur est survenue lors de l’arrêt des conteneurs.
    pause
    exit /b
)

echo ✅ Application arrêtée avec succès.
pause
