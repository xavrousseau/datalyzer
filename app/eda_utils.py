# app/eda_utils.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from scipy.stats import skew

sns.set(style="whitegrid")

# =========================================================
# OUTIL DE CONVERSION FIGURE ➜ base64 pour l'API
# =========================================================

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)
    return img_base64

# =========================================================
# 1. APERÇU GLOBAL
# =========================================================

def overview_report(df: pd.DataFrame) -> dict:
    return {
        "shape": df.shape,
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "n_unique": df.nunique().to_dict()
    }

def print_overview(df: pd.DataFrame) -> None:
    print(">> Dimensions :", df.shape)
    print(">> Colonnes :", df.columns.tolist())
    print("\n>> Types de données :\n", df.dtypes)
    print("\n>> Nombre de valeurs uniques :\n", df.nunique())
    print("\n>> Valeurs manquantes (par %):\n", df.isnull().mean().sort_values(ascending=False) * 100)

# =========================================================
# 2. VALEURS MANQUANTES
# =========================================================

def plot_missing_values(df: pd.DataFrame, threshold: float = 0.0) -> str | None:
    missing_pct = df.isnull().mean() * 100
    filtered = missing_pct[missing_pct > threshold].sort_values(ascending=False)

    if filtered.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=filtered.index, y=filtered.values, ax=ax)
    ax.set_ylabel("% de valeurs manquantes")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_title("Taux de valeurs manquantes")
    return fig_to_base64(fig)

# =========================================================
# 3. VARIABLES NUMÉRIQUES
# =========================================================

def analyze_numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    stats = df[numeric_cols].describe().T
    stats["skew"] = df[numeric_cols].apply(skew)
    return stats

def plot_numeric_distributions(df: pd.DataFrame) -> dict:
    results = {}
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    for col in numeric_cols:
        fig, ax = plt.subplots()
        sns.histplot(df[col].dropna(), kde=True, ax=ax)
        ax.set_title(f"Distribution : {col}")
        results[col] = fig_to_base64(fig)
    return results

def plot_boxplots(df: pd.DataFrame) -> dict:
    results = {}
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    for col in numeric_cols:
        fig, ax = plt.subplots()
        sns.boxplot(x=df[col], ax=ax, orient='h')
        ax.set_title(f"Boxplot : {col}")
        results[col] = fig_to_base64(fig)
    return results

# =========================================================
# 4. VARIABLES CATÉGORIELLES
# =========================================================

def analyze_categorical_features(df: pd.DataFrame, max_unique=20) -> dict:
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    result = {}
    for col in cat_cols:
        if df[col].nunique() <= max_unique:
            result[col] = df[col].value_counts(normalize=True).to_dict()
    return result

def plot_categorical_distributions(df: pd.DataFrame, max_unique=20) -> dict:
    results = {}
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        if df[col].nunique() <= max_unique:
            fig, ax = plt.subplots()
            sns.countplot(y=df[col], order=df[col].value_counts().index, ax=ax)
            ax.set_title(f"Répartition : {col}")
            results[col] = fig_to_base64(fig)
    return results

# =========================================================
# 5. CORRÉLATION
# =========================================================

def plot_correlation_matrix(df: pd.DataFrame, method='pearson') -> str:
    corr = df.corr(method=method)
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
    ax.set_title("Matrice de corrélation")
    return fig_to_base64(fig)

def get_highly_correlated_features(df: pd.DataFrame, threshold=0.8) -> list:
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

def analyze_target_relationships(df: pd.DataFrame, target: str) -> dict:
    if target not in df.columns:
        return {}

    figs = {}
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns.drop(target, errors='ignore')
    for col in num_cols:
        fig, ax = plt.subplots()
        sns.boxplot(x=df[target], y=df[col], ax=ax)
        ax.set_title(f"{col} en fonction de {target}")
        figs[col] = fig_to_base64(fig)
    return figs
