@echo off
cd ..

echo ========================================
echo ♻️ NETTOYAGE SÉCURISÉ DU PROJET DATALYZER
echo ========================================
echo.

:: Étape 1 : Arrêt propre des conteneurs liés au projet
echo ⛔ Arrêt des conteneurs Docker (si actifs)...
docker-compose down

:: Étape 2 : Suppression sécurisée des dossiers de travail générés
echo 🧼 Nettoyage des fichiers temporaires :
set FOLDERS=data\uploads data\exports logs

for %%F in (%FOLDERS%) do (
    if exist %%F (
        echo - Suppression du dossier : %%F
        rmdir /s /q %%F
    ) else (
        echo - Dossier non trouvé : %%F (déjà nettoyé ?)
    )
)

:: Étape 3 : Recréation des dossiers vides pour la relance propre
echo 🗂️ Recréation des répertoires nécessaires...
mkdir data\uploads
mkdir data\exports
mkdir logs

echo ✅ Nettoyage terminé. Le projet est prêt pour une nouvelle session.
pause
