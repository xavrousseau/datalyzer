Write-Host "🔍 Recherche et suppression des conteneurs datalyzer et hybrid_infra_project..." -ForegroundColor Cyan

# Supprimer les conteneurs liés à datalyzer
docker ps -a --filter "name=datalyzer" --format "{{.ID}}" | ForEach-Object {
    Write-Host "🗑 Suppression du conteneur Datalyzer $_" -ForegroundColor Yellow
    docker rm -f $_
}

# Supprimer les conteneurs liés à hybrid_infra_project
# docker ps -a --filter "name=hybrid_infra_project" --format "{{.ID}}" | ForEach-Object {
#     Write-Host "🗑 Suppression du conteneur HybridInfra $_" -ForegroundColor Yellow
#     docker rm -f $_
# }

Write-Host "✅ Conteneurs supprimés." -ForegroundColor Green

# Supprimer les images liées
Write-Host "`n🔍 Recherche et suppression des images Docker associées..." -ForegroundColor Cyan
docker images --filter=reference="*datalyzer*" --format "{{.ID}}" | ForEach-Object {
    Write-Host "🧱 Suppression de l'image $_" -ForegroundColor Yellow
    docker rmi -f $_
}
# docker images --filter=reference="*hybrid_infra_project*" --format "{{.ID}}" | ForEach-Object {
#     Write-Host "🧱 Suppression de l'image $_" -ForegroundColor Yellow
#     docker rmi -f $_
# }
Write-Host "✅ Images supprimées." -ForegroundColor Green

# Supprimer les réseaux personnalisés
Write-Host "`n🔌 Suppression des réseaux personnalisés..." -ForegroundColor Cyan
docker network rm datalyzer_eda-net 2>$null
# docker network rm hybrid_infra_project_default 2>$null
Write-Host "✅ Réseaux supprimés." -ForegroundColor Green

# (Optionnel) nettoyage de volumes Docker non utilisés
# Write-Host "`n📦 Nettoyage des volumes Docker non utilisés (optionnel)..." -ForegroundColor Cyan
# docker volume prune -f
# Write-Host "✅ Volumes inutilisés supprimés." -ForegroundColor Green

Write-Host "`n🎉 Nettoyage Docker terminé avec succès." -ForegroundColor Green
