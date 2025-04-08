@echo off
cd ..

echo ========================================
echo ♻️ NETTOYAGE SÉCURISÉ DU PROJET EDA EXPLORER
echo ========================================
echo.

:: Étape 1 : Arrêt des services du projet actuel
echo ⛔ Arrêt des conteneurs Docker de ce projet...
docker-compose down

:: Étape 2 : Suppression des fichiers générés localement
echo 🧼 Suppression des fichiers générés (data/uploads, data/exports, logs)...

rmdir /s /q data\uploads
rmdir /s /q data\exports
rmdir /s /q logs

mkdir data\uploads
mkdir data\exports
mkdir logs

echo ✅ Nettoyage terminé. Aucun autre projet Docker n’a été impacté.
pause
