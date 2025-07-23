# ============================================================
# Fichier : eda_utils.py
# Objectif : Fonctions utilitaires pour l'analyse exploratoire
# Version harmonisée pour Datalyzer + Améliorations
# ============================================================

import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.feature_selection import VarianceThreshold
from scipy.stats import chi2_contingency, zscore
import streamlit as st


# ============================================================
# 🔍 Typage & résumé
# ============================================================

def detect_variable_types(df: pd.DataFrame) -> dict:
    """Détecte les types de variables par analyse heuristique."""
    return {col: str(df[col].dtype) for col in df.columns}

@st.cache_data
def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne un résumé statistique rapide du DataFrame."""
    summary = {
        "Lignes": len(df),
        "Colonnes": len(df.columns),
        "Colonnes numériques": len(df.select_dtypes(include="number").columns),
        "Colonnes catégorielles": len(df.select_dtypes(include="object").columns),
        "Valeurs manquantes (%)": round(df.isna().mean().mean() * 100, 2),
        "Doublons": df.duplicated().sum()
    }
    return pd.DataFrame.from_dict(summary, orient="index", columns=["Valeur"])


def score_data_quality(df: pd.DataFrame) -> float:
    """
    Calcule un score global de qualité des données basé sur :
    - Pourcentage de valeurs manquantes
    - Taux de doublons
    - Colonnes constantes
    Renvoie un score sur 100 (plus élevé = meilleure qualité).
    """
    na_score = 100 - df.isna().mean().mean() * 100
    dup_score = 100 - (df.duplicated().sum() / len(df) * 100 if len(df) > 0 else 0)
    const_score = 100 - (len(detect_constant_columns(df)) / len(df.columns) * 100 if len(df.columns) > 0 else 0)
    return round((na_score + dup_score + const_score) / 3, 2)


# ============================================================
# 🩹 Valeurs manquantes
# ============================================================

def plot_missing_values(df: pd.DataFrame):
    """Crée un histogramme des colonnes avec valeurs manquantes."""
    na_ratio = df.isna().mean()
    na_df = na_ratio[na_ratio > 0].sort_values(ascending=False).reset_index()
    na_df.columns = ["Colonne", "Taux de NA"]
    return px.bar(na_df, x="Colonne", y="Taux de NA", title="Valeurs manquantes par colonne")

def get_columns_above_threshold(df: pd.DataFrame, seuil: float = 0.5) -> list:
    """Colonnes ayant un taux de NA supérieur à un seuil donné."""
    return df.columns[df.isna().mean() > seuil].tolist()

def drop_missing_columns(df: pd.DataFrame, seuil: float = 0.5) -> pd.DataFrame:
    """Supprime les colonnes trop remplies de NA (au-dessus du seuil)."""
    return df.drop(columns=get_columns_above_threshold(df, seuil))


# ============================================================
# 🎯 Colonnes peu informatives
# ============================================================

def detect_constant_columns(df: pd.DataFrame) -> list:
    """Colonnes avec une seule modalité (constantes)."""
    return [col for col in df.columns if df[col].nunique() <= 1]

def detect_low_variance_columns(df: pd.DataFrame, threshold: float = 0.01) -> list:
    """Colonnes numériques avec très faible variance."""
    numeric_cols = df.select_dtypes(include="number")
    if numeric_cols.empty:
        return []
    selector = VarianceThreshold(threshold)
    selector.fit(numeric_cols)
    return list(numeric_cols.columns[~selector.get_support()])


# ============================================================
# 🚨 Outliers & distributions
# ============================================================

def detect_outliers(df: pd.DataFrame, method: str = "iqr", seuil: float = 3.0) -> pd.DataFrame:
    """
    Détecte les outliers avec la méthode IQR ou Z-Score selon la colonne numérique.
    """
    outliers = pd.DataFrame()
    for col in df.select_dtypes(include="number").columns:
        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            mask = (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
        elif method == "zscore":
            z = np.abs(zscore(df[col].dropna()))
            mask = z > seuil
            mask = mask.reindex(df.index, fill_value=False)
        else:
            continue
        temp = df[mask].copy()
        temp["__outlier_sur__"] = col
        outliers = pd.concat([outliers, temp])
    return outliers

def detect_skewed_distributions(df: pd.DataFrame, seuil: float = 2.0) -> list:
    """Colonnes numériques avec une distribution asymétrique (skewness élevée)."""
    return [col for col in df.select_dtypes(include="number") if abs(df[col].skew()) > seuil]


# ============================================================
# 🔗 Corrélations (numériques)
# ============================================================

def compute_correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Retourne la matrice de corrélation des colonnes numériques."""
    return df.select_dtypes(include="number").corr(method=method)

def get_top_correlations(df: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Retourne les paires de variables les plus corrélées."""
    corr = df.select_dtypes(include="number").corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    return (
        upper.stack()
        .reset_index()
        .rename(columns={"level_0": "Var1", "level_1": "Var2", 0: "Correlation"})
        .sort_values("Correlation", ascending=False)
        .head(top)
    )


# ============================================================
# 🧮 Encodage
# ============================================================

def encode_categorical(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Encode les variables catégorielles sélectionnées en one-hot."""
    return pd.get_dummies(df, columns=cols)


# ============================================================
# 📊 Visualisation Num ↔ Cat
# ============================================================

def plot_boxplots(df: pd.DataFrame, numeric_col: str, cat_col: str):
    """Affiche un boxplot entre une variable numérique et une variable catégorielle."""
    return px.box(df, x=cat_col, y=numeric_col, points="outliers",
                  title=f"Boxplot : {numeric_col} par {cat_col}")


# ============================================================
# 🔠 Corrélations catégorielles (Cramér’s V)
# ============================================================

@st.cache_data
def compute_cramers_v_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule la matrice des corrélations Cramér’s V pour variables catégorielles."""
    cols = df.columns
    cramers_v = pd.DataFrame(index=cols, columns=cols)
    for col1 in cols:
        for col2 in cols:
            confusion = pd.crosstab(df[col1], df[col2])
            if confusion.empty:
                cramers_v.loc[col1, col2] = np.nan
                continue
            chi2 = chi2_contingency(confusion)[0]
            n = confusion.sum().sum()
            phi2 = chi2 / n
            r, k = confusion.shape
            phi2_corr = max(0, phi2 - ((k-1)*(r-1)) / (n-1))
            r_corr = r - ((r-1)**2)/(n-1)
            k_corr = k - ((k-1)**2)/(n-1)
            v = np.sqrt(phi2_corr / min((k_corr-1), (r_corr-1)))
            cramers_v.loc[col1, col2] = round(v, 3)
    return cramers_v.astype(float)
