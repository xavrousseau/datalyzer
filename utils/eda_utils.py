# ============================================================
# Fichier : eda_utils.py
# Objectif : Fonctions utilitaires pour l'analyse exploratoire (EDA)
# Version : harmonisée & durcie (anti-crash, UX stable, caches)
# ============================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import chi2_contingency, zscore

# ============================================================
# 🧩 Helpers génériques (types, coercition, sampling, affichage)
# ============================================================

def is_numeric(s: pd.Series) -> bool:
    """Retourne True si la série est de type numérique (bool, int, uint, float, complex)."""
    return s.dtype.kind in "biufc"

def to_numeric_safe(s: pd.Series) -> pd.Series:
    """
    Convertit souplement une série en numérique :
    - ne touche pas si déjà numérique
    - remplace les virgules décimales par des points
    - errors='coerce' pour éviter les exceptions (valeurs non convertibles -> NaN)
    """
    if is_numeric(s):
        return s
    return pd.to_numeric(s.replace({",": "."}, regex=True), errors="coerce")

def safe_sample(df: pd.DataFrame, n: int = 5000) -> pd.DataFrame:
    """Limite la taille pour les graphes/analyses lourdes (évite d'envoyer 1M de points à Plotly)."""
    if len(df) <= n:
        return df
    return df.sample(n, random_state=42)

def show_fig(fig):
    """Affiche une figure Plotly seulement si non nulle (évite les graphiques vides)."""
    if fig is None:
        st.info("Rien à afficher pour ce graphique.")
    else:
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 🔍 Typage & résumé
# ============================================================

def detect_variable_types(df: pd.DataFrame) -> dict:
    """Détecte les types de variables par analyse heuristique (simple introspection pandas)."""
    return {col: str(df[col].dtype) for col in df.columns}

@st.cache_data
def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retourne un résumé statistique rapide du DataFrame (tailles, nb de colonnes par type,
    taux moyen de NA, nb de doublons). Côté perf : cache car pur calcul déterministe.
    """
    summary = {
        "Lignes": len(df),
        "Colonnes": len(df.columns),
        "Colonnes numériques": len(df.select_dtypes(include="number").columns),
        "Colonnes catégorielles": len(df.select_dtypes(include="object").columns),
        "Valeurs manquantes (%)": round(df.isna().mean().mean() * 100, 2) if len(df.columns) else 0.0,
        "Doublons": df.duplicated().sum() if len(df) else 0
    }
    return pd.DataFrame.from_dict(summary, orient="index", columns=["Valeur"])

def score_data_quality(df: pd.DataFrame) -> float:
    """
    Score global (0-100) basé sur :
      - Pourcentage moyen de valeurs manquantes (moins = mieux)
      - Taux de doublons (moins = mieux)
      - Proportion de colonnes constantes (moins = mieux)
    """
    if len(df) == 0 or len(df.columns) == 0:
        return 100.0  # dataset vide = rien à reprocher côté "qualité formelle"
    na_score = 100 - df.isna().mean().mean() * 100
    dup_score = 100 - (df.duplicated().sum() / len(df) * 100)
    const_score = 100 - (len(detect_constant_columns(df)) / len(df.columns) * 100)
    return round((na_score + dup_score + const_score) / 3, 2)

# ============================================================
# 🩹 Valeurs manquantes
# ============================================================

def missing_stats(df: pd.DataFrame) -> pd.Series | None:
    """
    Renvoie une série (index=colonnes, valeurs=taux de NA) triée décroissante,
    ou None si aucune colonne n'a de NA.
    """
    if df.empty or df.shape[1] == 0:
        return None
    na = df.isna().mean().sort_values(ascending=False)
    na = na[na > 0]
    return na if not na.empty else None

def plot_missing_values(df: pd.DataFrame):
    """
    Bar chart des colonnes ayant des NA (>0). Retourne None si aucune NA,
    afin de laisser l'appelant gérer l'affichage conditionnel.
    """
    na = missing_stats(df)
    if na is None:
        return None
    na_df = na.reset_index()
    na_df.columns = ["Colonne", "Taux de NA"]
    return px.bar(na_df, x="Colonne", y="Taux de NA", title="Valeurs manquantes par colonne")

def get_columns_above_threshold(df: pd.DataFrame, seuil: float = 0.5) -> list[str]:
    """Liste des colonnes dont le taux de NA dépasse `seuil` (0.5 = 50%)."""
    if df.empty:
        return []
    return df.columns[df.isna().mean() > seuil].tolist()

def drop_missing_columns(df: pd.DataFrame, seuil: float = 0.5) -> pd.DataFrame:
    """Supprime les colonnes trop remplies de NA (au-dessus du seuil)."""
    cols = get_columns_above_threshold(df, seuil)
    return df.drop(columns=cols) if cols else df

# ============================================================
# 🎯 Colonnes peu informatives
# ============================================================

def detect_constant_columns(df: pd.DataFrame) -> list[str]:
    """Colonnes avec une seule modalité (constantes)."""
    return [col for col in df.columns if df[col].nunique(dropna=False) <= 1]

def detect_low_variance_columns(df: pd.DataFrame, threshold: float = 0.01) -> list[str]:
    """
    Colonnes numériques à très faible variance (via pandas, robuste aux NaN).
    Remarque : on utilise var(skipna=True) pour éviter les soucis de NaN.
    """
    num = df.select_dtypes(include="number")
    if num.empty:
        return []
    return [c for c in num.columns if (num[c].var(skipna=True) <= threshold or np.isnan(num[c].var(skipna=True)))]

# ============================================================
# 🚨 Outliers & distributions
# ============================================================

def detect_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    threshold: float = 3.0,
    **kwargs
) -> pd.DataFrame:
    """
    Détecte les outliers avec la méthode IQR ou Z-Score.

    Paramètres
    ----------
    method : {"iqr", "zscore"}
        - "iqr" : utilise l'intervalle interquartile (k * IQR)
        - "zscore" : utilise le score-z (|z| > seuil)
    threshold : float
        - pour IQR : multiplicateur k
        - pour Z-score : seuil de |z|
    kwargs :
        - compat : accepte aussi 'seuil' (alias historique de threshold)

    Retour
    ------
    DataFrame contenant uniquement les lignes outliers, avec une colonne
    supplémentaire "__outlier_sur__" indiquant la variable concernée.
    """
    thr = float(kwargs.get("seuil", threshold))  # compat 'seuil'
    outliers = pd.DataFrame()

    # On restreint aux colonnes numériques (avec coercition douce au besoin)
    num_cols = [c for c in df.columns if is_numeric(df[c]) or to_numeric_safe(df[c]).notna().any()]
    if not num_cols:
        return outliers

    for col in num_cols:
        s = to_numeric_safe(df[col])

        if method == "iqr":
            # Convention EDA : si l'appel laisse thr=3.0 par défaut, on prend k=1.5
            k = 1.5 if thr == 3.0 else thr
            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                mask_series = pd.Series(False, index=df.index)
            else:
                mask_series = (s < q1 - k * iqr) | (s > q3 + k * iqr)

        elif method == "zscore":
            s_notna = s.dropna()
            if s_notna.empty:
                mask_series = pd.Series(False, index=df.index)
            else:
                # zscore sur les index non-NA, puis réalignement sur l'index d'origine
                z = pd.Series(np.abs(zscore(s_notna)), index=s_notna.index)
                mask_series = pd.Series(False, index=df.index)
                mask_series.loc[z.index] = z > thr
        else:
            # Méthode inconnue : on ignore la colonne
            continue

        temp = df.loc[mask_series].copy()
        if not temp.empty:
            temp["__outlier_sur__"] = col
            outliers = pd.concat([outliers, temp], axis=0)

    return outliers

def detect_skewed_distributions(df: pd.DataFrame, seuil: float = 2.0) -> list[str]:
    """
    Colonnes numériques avec une distribution asymétrique (|skewness| > seuil).
    On applique une coercition douce pour supporter les colonnes 'mixtes'.
    """
    cols = []
    for col in df.columns:
        s = to_numeric_safe(df[col])
        if is_numeric(s):
            val = s.skew(skipna=True)
            if pd.notna(val) and abs(val) > seuil:
                cols.append(col)
    return cols

# ============================================================
# 🔗 Corrélations (numériques)
# ============================================================

@st.cache_data
def compute_correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """
    Matrice de corrélation des colonnes numériques (cache pour accélérer l'UI).
    Retourne un DataFrame vide si < 2 colonnes numériques.
    """
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        return pd.DataFrame()
    return num.corr(method=method)

def get_top_correlations(df: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """
    Retourne les paires (var1, var2, corr) les plus corrélées en valeur absolue.
    Si < 2 colonnes numériques, renvoie un DataFrame vide avec les bonnes colonnes.
    """
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        return pd.DataFrame(columns=["var1", "var2", "corr"])
    corr = num.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    pairs = (
        upper.stack()
             .sort_values(ascending=False)
             .reset_index()
             .rename(columns={"level_0": "var1", "level_1": "var2", 0: "corr"})
    )
    return pairs.head(top)

# ============================================================
# 🧮 Encodage
# ============================================================

def encode_categorical(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    One-hot encoding (get_dummies) sur les colonnes sélectionnées.
    Astuce : drop_first=False par défaut pour rester neutre (pas d'info perdue).
    """
    if not cols:
        return df
    valid = [c for c in cols if c in df.columns]
    if not valid:
        return df
    return pd.get_dummies(df, columns=valid)

# ============================================================
# 📊 Visualisation Num ↔ Cat
# ============================================================

def plot_boxplots(df: pd.DataFrame, numeric_col: str, cat_col: str):
    """
    Boxplot d'une variable numérique par modalité d'une variable catégorielle.
    Renvoie None si la colonne numérique n'est pas exploitable (ex : toute NaN).
    """
    if numeric_col not in df.columns or cat_col not in df.columns:
        return None
    y = to_numeric_safe(df[numeric_col])
    if y.dropna().empty:
        return None
    return px.box(pd.DataFrame({cat_col: df[cat_col], numeric_col: y}),
                  x=cat_col, y=numeric_col, points="outliers",
                  title=f"Boxplot : {numeric_col} par {cat_col}")

# ============================================================
# 🔠 Corrélations catégorielles (Cramér’s V)
# ============================================================

@st.cache_data
def compute_cramers_v_matrix(df: pd.DataFrame, max_levels: int = 50) -> pd.DataFrame:
    """
    Matrice Cramér’s V pour variables catégorielles (object/category) seulement,
    en ignorant les colonnes à trop forte cardinalité pour éviter les crosstabs énormes.
    Correction de biais de Bergsma (phi2_corr).
    """
    # Colonnes catégorielles "raisonnables"
    cat_cols = [
        c for c in df.columns
        if (df[c].dtype == "object" or str(df[c].dtype).startswith("category"))
    ]
    cat_cols = [c for c in cat_cols if df[c].nunique(dropna=False) <= max_levels]

    if len(cat_cols) < 2:
        # Retourne une matrice vide ou 1x1 selon le cas pour éviter les plantages d'affichage
        return pd.DataFrame(index=cat_cols, columns=cat_cols, dtype=float)

    cramers_v = pd.DataFrame(index=cat_cols, columns=cat_cols, dtype=float)

    for col1 in cat_cols:
        for col2 in cat_cols:
            confusion = pd.crosstab(df[col1], df[col2])
            if confusion.empty:
                cramers_v.loc[col1, col2] = np.nan
                continue

            chi2 = chi2_contingency(confusion)[0]
            n = confusion.to_numpy().sum()
            if n <= 1:
                cramers_v.loc[col1, col2] = np.nan
                continue

            phi2 = chi2 / n
            r, k = confusion.shape

            # Correction de biais (recommandée pour Cramér sur tableaux non immenses)
            phi2_corr = max(0, phi2 - ((k - 1) * (r - 1)) / max(n - 1, 1))
            r_corr = r - ((r - 1) ** 2) / max(n - 1, 1)
            k_corr = k - ((k - 1) ** 2) / max(n - 1, 1)
            denom = min((k_corr - 1), (r_corr - 1))

            v = np.sqrt(phi2_corr / denom) if denom > 0 else np.nan
            cramers_v.loc[col1, col2] = round(float(v), 3) if pd.notna(v) else np.nan

    return cramers_v
