@echo off
cd ..

echo ========================================
echo 🧨 SUPPRESSION DES IMAGES DOCKER LIEES À DATALYZER
echo ========================================
echo.

:: Suppression explicite de l’image principale définie dans Dockerfile.streamlit
set IMAGE=datalyzer-app_streamlit
echo 🔥 Suppression manuelle de l’image : %IMAGE%:latest
docker image rm %IMAGE%:latest

:: Suppression de toutes les autres images contenant "datalyzer"
echo 🔍 Recherche d’images Docker contenant 'datalyzer'...
docker images | findstr datalyzer > temp_images.txt

echo 🔥 Suppression automatique des images listées :
for /F "tokens=3" %%i in (temp_images.txt) do (
    echo - Suppression de l’image : %%i
    docker rmi -f %%i
)

:: Nettoyage du fichier temporaire
del temp_images.txt >nul 2>&1

echo ✅ Toutes les images liées à 'datalyzer' ont été supprimées.
pause
