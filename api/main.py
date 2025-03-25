# =============================================================================
# IMPORTATION DES LIBRAIRIES
# =============================================================================

# FastAPI : Framework permettant de créer des API web rapides et performantes.
from fastapi import FastAPI, UploadFile, File

# fastapi.responses fournit des classes de réponses HTTP pour renvoyer du JSON ou des fichiers.
from fastapi.responses import JSONResponse, FileResponse

# Pydantic : bibliothèque pour la validation des données via des modèles (ici utilisé pour le modèle de suppression de colonnes).
from pydantic import BaseModel

# typing.List permet d'indiquer le type d'une liste dans les annotations.
from typing import List

# pandas est utilisé pour manipuler et analyser des données sous forme de DataFrame.
import pandas as pd

# numpy est utilisé pour les opérations numériques et mathématiques.
import numpy as np

# os permet d'interagir avec le système de fichiers (création de dossiers, chemin d'accès, etc.).
import os

# io permet de traiter des flux de données (par exemple, convertir des données binaires en format lisible par pandas).
import io


# =============================================================================
# ⚙️ CONFIGURATION DE L'API
# =============================================================================

# Création de l'application FastAPI avec un titre personnalisé.
app = FastAPI(title="EDA Backend API")

# Définition du répertoire où seront stockés les fichiers uploadés.
UPLOAD_DIR = "data/uploads"
# Crée le dossier "data/uploads" s'il n'existe pas déjà.
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Stockage temporaire en mémoire du DataFrame chargé.
# Ce dictionnaire servira de cache pour stocker les données durant la session.
DATA_STORE = {"df": None}


# =============================================================================
# 🔧 UTILITAIRE : NETTOYAGE POUR JSON
# =============================================================================
def make_json_safe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remplace toutes les valeurs non compatibles JSON par None.
    
    Certains types de valeurs (comme NaN, inf, -inf, NA, NaT) ne peuvent pas être 
    sérialisés en JSON. Cette fonction remplace ces valeurs par None afin de garantir 
    la compatibilité avec JSON.
    
    Args:
        df (pd.DataFrame): Le DataFrame à nettoyer.
    
    Returns:
        pd.DataFrame: Le DataFrame avec les valeurs incompatibles remplacées par None.
    """
    df = df.replace({
        float('inf'): None,
        float('-inf'): None,
        pd.NaT: None,
        pd.NA: None,
        np.nan: None
    })
    # La méthode where remplace toutes les valeurs non-nulles par elles-mêmes, et les valeurs nulles par None.
    return df.where(pd.notnull(df), None)


# =============================================================================
# 🌐 ENDPOINT RACINE
# =============================================================================
@app.get("/")
def root():
    """
    Endpoint racine de l'API.
    
    Retourne un message de bienvenue, la liste des endpoints disponibles 
    et l'URL de la documentation interactive (/docs).
    """
    return {
        "message": "🎉 Bienvenue sur l'API EDA Explorer !",
        "endpoints_disponibles": [
            "/upload/",
            "/head/",
            "/missing-values/",
            "/describe/",
            "/duplicates/",
            "/drop-duplicates/",
            "/drop-columns/",
            "/export/",
            "/report/"
        ],
        "docs": "/docs"
    }


# =============================================================================
# 📦 MODÈLE PYDANTIC POUR LA SUPPRESSION DE COLONNES
# =============================================================================
class ColumnDropRequest(BaseModel):
    """
    Modèle de données pour la requête de suppression de colonnes.
    
    Attributes:
        columns (List[str]): Liste des noms de colonnes à supprimer.
    """
    columns: List[str]


# =============================================================================
# 📤 UPLOAD D’UN FICHIER CSV
# =============================================================================
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    """
    Endpoint pour uploader un fichier CSV.
    
    Processus :
    1. Lecture asynchrone du contenu du fichier uploadé.
    2. Conversion du contenu en DataFrame à l'aide de pd.read_csv (via un flux BytesIO).
    3. Stockage du DataFrame dans DATA_STORE pour utilisation ultérieure.
    4. Retourne des métadonnées sur le fichier (nom, colonnes et nombre de lignes).
    
    En cas d'erreur, renvoie une réponse JSON avec le message d'erreur.
    """
    try:
        # Lecture du contenu du fichier en mémoire (données binaires)
        contents = await file.read()
        # Conversion du contenu en DataFrame en utilisant BytesIO pour créer un flux lisible par pandas.
        df = pd.read_csv(io.BytesIO(contents))
        # Stockage temporaire du DataFrame dans DATA_STORE.
        DATA_STORE["df"] = df
        # Retourne les métadonnées du fichier uploadé.
        return {
            "filename": file.filename,
            "columns": df.columns.tolist(),
            "rows": len(df)
        }
    except Exception as e:
        # En cas d'erreur, renvoie une réponse d'erreur détaillée.
        return JSONResponse(status_code=400, content={"error": str(e)})


# =============================================================================
# 👀 AFFICHAGE DES PREMIÈRES LIGNES
# =============================================================================
@app.get("/head/")
def get_head(n: int = 5):
    """
    Endpoint pour récupérer les 'n' premières lignes du DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame a été chargé.
    2. Extrait les premières lignes avec la méthode head().
    3. Applique make_json_safe pour remplacer les valeurs incompatibles JSON par None.
    4. Retourne le résultat sous forme d'une liste de dictionnaires.
    
    Args:
        n (int): Nombre de lignes à retourner (par défaut 5).
    """
    df = DATA_STORE.get("df")
    if df is None:
        # Si aucun fichier n'est chargé, renvoie un message d'erreur.
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Extraction des n premières lignes et nettoyage pour JSON.
    head_df = make_json_safe(df.head(n))
    return head_df.to_dict(orient="records")


# =============================================================================
# 🧼 DÉTAILS DES VALEURS MANQUANTES
# =============================================================================
@app.get("/missing-values/")
def get_missing_values():
    """
    Endpoint pour obtenir le détail des valeurs manquantes dans le DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Calcule le nombre de valeurs manquantes par colonne.
    3. Calcule le pourcentage de valeurs manquantes pour chaque colonne.
    4. Retourne uniquement les colonnes présentant des valeurs manquantes.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    
    # Calcul du nombre de valeurs manquantes par colonne.
    missing = df.isnull().sum()
    # Calcul du pourcentage de valeurs manquantes par colonne.
    percent = (missing / len(df)) * 100
    # Création d'un DataFrame récapitulatif.
    result = pd.DataFrame({
        "column": missing.index,
        "missing_count": missing.values,
        "missing_percent": percent.values
    })
    # Retourne uniquement les colonnes où le nombre de valeurs manquantes est supérieur à 0.
    return result[result["missing_count"] > 0].to_dict(orient="records")


# =============================================================================
# 📊 STATISTIQUES DESCRIPTIVES
# =============================================================================
@app.get("/describe/")
def get_description():
    """
    Endpoint pour générer des statistiques descriptives du DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Calcule un résumé statistique en utilisant la méthode describe() de pandas.
    3. Nettoie le résumé via make_json_safe pour garantir la compatibilité JSON.
    4. Retourne le résumé sous forme de dictionnaire.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Calcul du résumé descriptif et nettoyage pour JSON.
    desc = make_json_safe(df.describe(include="all"))
    return desc.to_dict()


# =============================================================================
# 📦 DÉTECTION DE DOUBLONS
# =============================================================================
@app.get("/duplicates/")
def get_duplicates():
    """
    Endpoint pour détecter les doublons dans le DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Utilise la méthode duplicated() pour identifier les lignes dupliquées.
    3. Retourne le nombre de lignes dupliquées et le pourcentage par rapport au total.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Identification des doublons dans le DataFrame.
    dup = df[df.duplicated()]
    return {
        "duplicate_rows": len(dup),
        "percentage": round(100 * len(dup) / len(df), 2)
    }


# =============================================================================
# 🧹 SUPPRESSION DES DOUBLONS
# =============================================================================
@app.post("/drop-duplicates/")
def drop_duplicates():
    """
    Endpoint pour supprimer les doublons du DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Supprime les doublons en réinitialisant l'index.
    3. Met à jour DATA_STORE avec le DataFrame nettoyé.
    4. Retourne le nombre de doublons supprimés et le nombre de lignes restantes.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    before = len(df)  # Nombre de lignes avant suppression des doublons.
    df_cleaned = df.drop_duplicates().reset_index(drop=True)
    DATA_STORE["df"] = df_cleaned  # Mise à jour du DataFrame stocké.
    after = len(df_cleaned)  # Nombre de lignes après suppression.
    return {"removed": before - after, "remaining_rows": after}


# =============================================================================
# 🗑 SUPPRESSION DE COLONNES
# =============================================================================
@app.post("/drop-columns/")
def drop_columns(request: ColumnDropRequest):
    """
    Endpoint pour supprimer des colonnes spécifiques du DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Vérifie que les colonnes demandées existent dans le DataFrame.
    3. Supprime les colonnes spécifiées.
    4. Met à jour DATA_STORE et retourne un message de confirmation.
    
    Args:
        request (ColumnDropRequest): Modèle contenant la liste des colonnes à supprimer.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Vérifie que toutes les colonnes à supprimer existent.
    missing = [col for col in request.columns if col not in df.columns]
    if missing:
        return JSONResponse(status_code=400, content={"error": f"Colonnes introuvables : {missing}"})
    # Suppression des colonnes spécifiées.
    df.drop(columns=request.columns, inplace=True)
    DATA_STORE["df"] = df
    return {"message": f"{len(request.columns)} colonnes supprimées avec succès."}


# =============================================================================
# 📁 EXPORT DU CSV NETTOYÉ
# =============================================================================
@app.get("/export/")
def export_csv():
    """
    Endpoint pour exporter le DataFrame nettoyé au format CSV.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Sauvegarde le DataFrame dans un fichier CSV dans le dossier UPLOAD_DIR.
    3. Retourne le fichier CSV via FileResponse pour permettre son téléchargement.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Définition du chemin pour sauvegarder le fichier CSV.
    path = os.path.join(UPLOAD_DIR, "data_cleaned.csv")
    df.to_csv(path, index=False)
    return FileResponse(path, media_type="text/csv", filename="data_cleaned.csv")


# =============================================================================
# 📈 EXPORT D’UN RAPPORT SIMPLE (DESCRIBE)
# =============================================================================
@app.get("/report/")
def generate_report():
    """
    Endpoint pour générer un rapport simple des statistiques descriptives du DataFrame.
    
    Processus :
    1. Vérifie que le DataFrame est chargé.
    2. Calcule un résumé statistique à l'aide de la méthode describe(), le transpose.
    3. Exporte le résumé au format CSV dans le dossier UPLOAD_DIR.
    4. Retourne le fichier CSV du rapport via FileResponse pour téléchargement.
    """
    df = DATA_STORE.get("df")
    if df is None:
        return JSONResponse(status_code=404, content={"error": "Aucun fichier chargé."})
    # Définition du chemin pour sauvegarder le rapport CSV.
    path = os.path.join(UPLOAD_DIR, "eda_report.csv")
    df.describe(include="all").transpose().to_csv(path)
    return FileResponse(path, media_type="text/csv", filename="eda_report.csv")
