# ==============================
# 📌 IMPORTS
# ==============================
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import pandas as pd
import io
import chardet
import logging

# 📌 Importation des modules d'analyse (EDA)
from app.eda_utils import (
    overview_report,
    analyze_numeric_features,
    plot_missing_values,
    plot_correlation_matrix,
    plot_numeric_distributions,
    plot_boxplots,
    analyze_categorical_features,
    plot_categorical_distributions
)

# ==============================
# 📌 CONFIGURATION DES LOGS
# ==============================
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================
# 📌 INITIALISATION DE L'API
# ==============================
app = FastAPI(
    title="Datalyzer API",
    description="API pour explorer rapidement un jeu de données (EDA automatique)",
    version="0.3.2"
)

logging.info("🚀 Démarrage de l'API - Version 0.3.2")

# ==============================
# 📌 FONCTIONS UTILITAIRES
# ==============================

def detect_encoding(file_bytes):
    """
    Détecte l'encodage d'un fichier en utilisant `chardet`.
    Si l'encodage n'est pas détecté avec une confiance suffisante, essaie une liste d'encodages courants.
    """
    sample = file_bytes[:10000]  # Lire les 10 000 premiers octets
    result = chardet.detect(sample)
    detected_encoding = result["encoding"]
    confidence = result["confidence"]

    logging.info(f"🔍 Encodage détecté: {detected_encoding} (Confiance: {confidence})")

    if confidence > 0.5 and detected_encoding:
        return detected_encoding
    
    for enc in ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1", "cp1252"]:
        try:
            file_bytes.decode(enc)  # Test de décodage
            return enc
        except UnicodeDecodeError:
            continue

    return "utf-8"  # Dernier recours

def detect_separator(decoded_data):
    """
    Détecte automatiquement le séparateur du fichier CSV parmi les plus courants.
    """
    delimiters = [",", ";", "\t", "|"]
    samples = decoded_data.split("\n")[:10]  # Prend les 10 premières lignes
    detected_separators = {sep: sum(line.count(sep) for line in samples) for sep in delimiters}

    best_sep = max(detected_separators, key=detected_separators.get, default=",")
    logging.info(f"🔍 Séparateur détecté : {best_sep}")
    return best_sep

# ==============================
# 📌 ROUTE PRINCIPALE DE L'API
# ==============================

@app.post("/eda/")
async def run_eda(
    file: UploadFile = File(...), 
    encoding: str = Form("auto"), 
    separator: str = Form("auto")
):
    """
    Upload d'un fichier CSV, détection automatique de l'encodage et du séparateur, puis exécution de l'EDA.
    """
    try:
        # 📌 Lecture du fichier
        contents = await file.read()

        # 🔹 Détection automatique de l'encodage si nécessaire
        if encoding == "auto":
            encoding = detect_encoding(contents)
        logging.info(f"📝 Encodage utilisé : {encoding}")

        # 🔹 Tentative de décodage avec correction automatique
        try:
            decoded_data = contents.decode(encoding, errors="replace")  # Remplace les erreurs au lieu de planter
        except UnicodeDecodeError:
            return JSONResponse(
                content={"error": f"❌ Impossible de décoder en {encoding}. Essayez un autre encodage."},
                status_code=400
            )

        # 🔹 Détection du séparateur si nécessaire
        if separator == "auto":
            separator = detect_separator(decoded_data)
        logging.info(f"📝 Séparateur utilisé : {separator}")

        # 🔍 DEBUG : Prévisualisation des 500 premiers caractères
        logging.debug(f"📄 Prévisualisation des données : {decoded_data[:500]}")

        # 🔹 Chargement du fichier CSV
        try:
            df = pd.read_csv(io.StringIO(decoded_data), sep=separator, dtype=str, engine="python")
            logging.info("✅ Fichier chargé avec succès !")
        except pd.errors.ParserError as e:
            logging.error(f"❌ Erreur lors du parsing du fichier CSV : {e}")
            return JSONResponse(
                content={"error": "❌ Erreur lors du parsing du fichier CSV. Vérifiez le format."},
                status_code=400
            )

        # 🔹 Vérification et conversion des colonnes numériques
        for col in df.columns:
            if df[col].dtype == 'object':  # Vérifier si la colonne est une chaîne de caractères
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')  # Convertir, sinon NaN
                except Exception as e:
                    logging.warning(f"⚠️ Problème de conversion sur la colonne '{col}': {e}")

        # 🔹 Reconvertir les colonnes catégoriques en string pour éviter les erreurs
        for col in df.select_dtypes(include=['number']).columns:
            if df[col].nunique() < 20:  # Si peu de valeurs uniques, considérer comme catégorique
                df[col] = df[col].astype(str)

        # 🔹 Construction du rapport EDA
        report = {
            "overview": overview_report(df),
            "numeric_stats": analyze_numeric_features(df).round(2).fillna(" ").to_dict(),
            "correlation_matrix_base64": plot_correlation_matrix(df),
            "missing_values_plot_base64": plot_missing_values(df),
            "numeric_distributions_base64": plot_numeric_distributions(df),
            "boxplots_base64": plot_boxplots(df),
            "categorical_frequencies": analyze_categorical_features(df),
            "categorical_distributions_base64": plot_categorical_distributions(df)
        }

        logging.info("✅ Rapport EDA généré avec succès")
        return report

    except Exception as e:
        logging.error(f"❌ Erreur lors du traitement du fichier : {str(e)}")
        return JSONResponse(content={"error": f"Erreur lors du traitement du fichier : {str(e)}"}, status_code=500)

# ==============================
# 📌 TEST LORS DU LANCEMENT
# ==============================
if __name__ == "__main__":
    import uvicorn
    logging.info("🚀 Lancement du serveur Uvicorn")
    uvicorn.run(app, host="127.0.0.1", port=8600, log_level="debug")