# app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import io

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

app = FastAPI(
    title="Datalyzer API",
    description="API pour explorer rapidement un jeu de données (EDA automatique)",
    version="0.2.0"
)


@app.get("/")
def root():
    return {
        "message": "Bienvenue sur Datalyzer API 👋",
        "docs_url": "/docs",
        "endpoints": ["/eda/"],
        "auteur": "Ludovic Marchetti"
    }


@app.post("/eda/")
async def run_eda(file: UploadFile = File(...)):
    """
    Upload d'un fichier CSV, exécution d'une EDA complète, retour JSON (stats + images base64).
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        # Construction du rapport
        report = {
            "overview": overview_report(df),
            "numeric_stats": analyze_numeric_features(df).round(2).fillna("").to_dict(),
            "correlation_matrix_base64": plot_correlation_matrix(df),
            "missing_values_plot_base64": plot_missing_values(df),
            "numeric_distributions_base64": plot_numeric_distributions(df),  # {col: base64}
            "boxplots_base64": plot_boxplots(df),                             # {col: base64}
            "categorical_frequencies": analyze_categorical_features(df),      # {col: {val: freq}}
            "categorical_distributions_base64": plot_categorical_distributions(df)  # {col: base64}
        }

        return report

    except Exception as e:
        return JSONResponse(
            content={"error": f"Erreur lors du traitement du fichier : {str(e)}"},
            status_code=500
        )
