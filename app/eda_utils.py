from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from typing import Optional

app = FastAPI()

# =========================================================
# 1. APERÇU GLOBAL
# =========================================================

@app.get("/overview", response_class=HTMLResponse)
async def overview(df: pd.DataFrame):
    overview_data = {
        "shape": df.shape,
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "n_unique": df.nunique().to_dict()
    }
    return overview_data

# =========================================================
# 2. VALEURS MANQUANTES
# =========================================================

@app.get("/missing_values", response_class=HTMLResponse)
async def missing_values(df: pd.DataFrame, threshold: float = 0.0):
    missing_pct = df.isnull().mean() * 100
    filtered = missing_pct[missing_pct > threshold].sort_values(ascending=False)

    if filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune valeur manquante au-dessus du seuil.")

    fig = px.bar(filtered, x=filtered.index, y=filtered.values, labels={"x": "Colonnes", "y": "% de valeurs manquantes"})
    fig.update_layout(title="Taux de valeurs manquantes", xaxis_tickangle=-45)
    return fig.to_html()

# =========================================================
# 3. VARIABLES NUMÉRIQUES
# =========================================================

@app.get("/numeric_distributions", response_class=HTMLResponse)
async def numeric_distributions(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=["number"]).columns
    plots = {}
    for col in numeric_cols:
        fig = px.histogram(df, x=col, title=f"Distribution : {col}")
        plots[col] = fig.to_html()
    return "<br>".join(plots.values())

@app.get("/boxplots", response_class=HTMLResponse)
async def boxplots(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=["number"]).columns
    plots = {}
    for col in numeric_cols:
        fig = px.box(df, y=col, title=f"Boxplot : {col}")
        plots[col] = fig.to_html()
    return "<br>".join(plots.values())

# =========================================================
# 4. VARIABLES CATÉGORIELLES
# =========================================================

@app.get("/categorical_distributions", response_class=HTMLResponse)
async def categorical_distributions(df: pd.DataFrame, max_unique: int = 20):
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    plots = {}
    for col in cat_cols:
        if df[col].nunique() <= max_unique:
            fig = px.bar(df[col].value_counts(), title=f"Répartition : {col}")
            plots[col] = fig.to_html()
    return "<br>".join(plots.values())

# =========================================================
# 5. CORRÉLATION
# =========================================================

@app.get("/correlation_matrix", response_class=HTMLResponse)
async def correlation_matrix(df: pd.DataFrame, method: str = 'pearson'):
    corr = df.corr(method=method)
    fig = px.imshow(corr, text_auto=True, title="Matrice de corrélation")
    return fig.to_html()

@app.get("/highly_correlated_features", response_class=HTMLResponse)
async def highly_correlated_features(df: pd.DataFrame, threshold: float = 0.8):
    corr_matrix = df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    result = [
        {"feature_1": col, "feature_2": row, "correlation": upper.loc[row, col]}
        for col in upper.columns for row in upper.index
        if upper.loc[row, col] > threshold
    ]
    return result

# =========================================================
# 6. RELATION AVEC LA CIBLE
# =========================================================

@app.get("/target_relationships", response_class=HTMLResponse)
async def target_relationships(df: pd.DataFrame, target: str):
    if target not in df.columns:
        raise HTTPException(status_code=404, detail=f"La cible '{target}' n'est pas dans le DataFrame.")

    num_cols = df.select_dtypes(include=['float64', 'int64']).columns.drop(target, errors='ignore')
    plots = {}
    for col in num_cols:
        fig = px.box(df, x=target, y=col, title=f"{col} en fonction de {target}")
        plots[col] = fig.to_html()
    return "<br>".join(plots.values())

# =========================================================
# CHARGEMENT DU DATAFRAME (EXEMPLE)
# =========================================================

def load_data():
    # Exemple de chargement de données
    data = {
        "age": [25, 30, 35, 40, 45],
        "salary": [50000, 60000, 70000, 80000, 90000],
        "department": ["HR", "IT", "IT", "HR", "Finance"],
        "target": [0, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)

# Route pour tester l'API
@app.get("/test")
async def test():
    df = load_data()
    return await overview(df)