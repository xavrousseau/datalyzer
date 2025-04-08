@echo off
cd ..

echo ========================================
echo 🧨 SUPPRESSION DES IMAGES DOCKER DU PROJET EDA EXPLORER
echo ========================================
echo.

:: Nom des images à supprimer (personnalise-les si besoin)
set IMAGE1=datalyzer-fastapi
set IMAGE2=datalyzer-streamlit

:: Suppression de l’image FastAPI
echo 🔥 Suppression de l’image : %IMAGE1%
docker image rm %IMAGE1%:latest

:: Suppression de l’image Streamlit
echo 🔥 Suppression de l’image : %IMAGE2%
docker image rm %IMAGE2%:latest

echo ✅ Images spécifiques du projet supprimées. Les autres projets Docker ne sont PAS affectés.
pause
