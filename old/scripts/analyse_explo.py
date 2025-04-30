# ========================================================================
# sections/analyse_explo.py
#
# Ce script utilise Streamlit pour effectuer une analyse exploratoire
# sur un DataFrame. Il met en place plusieurs onglets pour visualiser :
# - Les types et caractéristiques des colonnes
# - Les données manquantes
# - Les distributions des variables
# - La détection d'outliers
# - Les statistiques descriptives
# - Des opérations de nettoyage automatique
# - Les corrélations entre variables
#
# Des utilitaires personnalisés sont importés pour faciliter l'EDA, la journalisation
# des transformations et la sauvegarde de snapshots du dataset.
# ========================================================================

import streamlit as st         # Permet de créer des applications web interactives pour l'analyse de données.
import pandas as pd            # Librairie de manipulation et d'analyse de données.
import plotly.express as px    # Librairie de visualisations graphiques interactives.

# Importation des fonctions utilitaires pour l'analyse exploratoire depuis le module utils.eda_utils.
from utils.eda_utils import (
    detect_constant_columns,       # Renvoie les colonnes du DataFrame qui n'ont qu'une seule valeur.
    detect_low_variance_columns,     # Renvoie les colonnes présentant une faible variance, potentiellement non informatives.
    detect_outliers_iqr,             # Détecte les valeurs aberrantes (outliers) en utilisant la méthode de l'IQR.
    get_columns_above_threshold,     # Retourne les colonnes dont le pourcentage de valeurs manquantes dépasse un seuil donné.
    drop_missing_columns,            # Fonction pour supprimer les colonnes avec trop de valeurs manquantes.
    plot_missing_values              # Génère un graphique interactif montrant la répartition des valeurs manquantes.
)

# Importation des fonctions de log et de sauvegarde des snapshots pour tracer les transformations du dataset.
from utils.log_utils import log_transformation   # Journalise les transformations appliquées sur le dataset.
from utils.snapshot_utils import save_snapshot     # Sauvegarde un instantané (snapshot) du dataset ou d'étapes clés.

# ----------------------------------------------------------------------------
# Fonction utilitaire : résumé synthétique d’un DataFrame
# Crée un résumé présentant, pour chaque colonne, son nom, son type, le nombre
# de valeurs uniques et un exemple de valeur non nulle.
# ----------------------------------------------------------------------------
def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Colonne": df.columns,
        "Type pandas": df.dtypes.astype(str),
        "Nb valeurs uniques": df.nunique(),
        "Exemple": [
            df[col].dropna().astype(str).unique()[0] if df[col].dropna().shape[0] > 0 else "—"
            for col in df.columns
        ]
    })

# ----------------------------------------------------------------------------
# Fonction pour marquer une étape comme validée et sauvegarder un snapshot
# Cette fonction met à jour l'état de session de Streamlit, sauvegarde un snapshot
# et affiche un message de succès.
# ----------------------------------------------------------------------------
def mark_step_done(step: str, custom_name: str = None):
    if "validation_steps" not in st.session_state:
        st.session_state["validation_steps"] = {}
    # Marque l'étape comme validée dans la session
    st.session_state["validation_steps"][step] = True
    # Utilise le nom personnalisé pour le snapshot si fourni, sinon génère un nom par défaut
    label = custom_name if custom_name else f"{step}_validated"
    # Sauvegarde un snapshot avec le label défini
    save_snapshot(label=label)
    st.success("✅ Étape validée. Snapshot sauvegardé.")

# ----------------------------------------------------------------------------
# Bouton de validation avec champ optionnel pour le nom du snapshot.
# Affiche un champ de saisie et un bouton, puis valide l'étape si le bouton est cliqué.
# ----------------------------------------------------------------------------
def validate_step_button(step_name: str, label: str = "✅ Valider l’étape"):
    # Permet de saisir un nom personnalisé pour le snapshot (optionnel)
    name = st.text_input(f"Nom du snapshot pour l'étape `{step_name}` (optionnel)", key=f"name_{step_name}")
    # Bouton de validation qui, lorsqu'il est cliqué, valide l'étape via la fonction mark_step_done.
    if st.button(label, key=f"step_{step_name}"):
        mark_step_done(step_name, custom_name=name)

# ----------------------------------------------------------------------------
# Fonction principale pour lancer l'analyse exploratoire
# Elle organise l'affichage de plusieurs onglets, chacun dédié à une facette de l'EDA.
# ----------------------------------------------------------------------------
def run_analyse_exploratoire(df):
    # Affiche un sous-titre pour la section d'analyse exploratoire
    st.subheader("🔍 Analyse exploratoire")

    # Définition des étapes de l'analyse avec un label court pour chaque section
    steps = {
        "types": "🧾 Types",
        "missing": "❓ Manquants",
        "histos": "📊 Distributions",
        "outliers": "🚨 Outliers",
        "stats": "📈 Stats",
        "cleaning": "🧹 Nettoyage",
        "correlations": "🔗 Corrélations"
    }

    # Bandeau latéral affichant la progression (étapes validées ou non)
    st.sidebar.markdown("### 🗂️ Progression")
    for key, label in steps.items():
        status = "✅" if st.session_state.get("validation_steps", {}).get(key) else "⬜"
        st.sidebar.write(f"{status} {label}")

    # Création d'un ensemble d'onglets pour chaque étape
    tabs = st.tabs(list(steps.values()))

    # ================================================
    # Onglet 1 — Types de colonnes
    # ================================================
    with tabs[0]:
        st.markdown("### 🧬 Vue d'ensemble des types de colonnes")
        st.markdown("""
        Cet onglet permet d’**inspecter chaque colonne du dataset** :
        - Son type (`int`, `float`, `object`, etc.),
        - Son nombre de valeurs uniques,
        - Un exemple de valeur présente.
        
        Cela aide à détecter rapidement des colonnes suspectes, comme des identifiants ou des colonnes constantes.
        """)
        # Génère un résumé synthétique du DataFrame
        summary = summarize_dataframe(df)
        st.dataframe(summary, use_container_width=True)
        # Affiche un résumé global du nombre de colonnes et des colonnes constantes
        st.markdown(f"""
        - Total de colonnes : **{df.shape[1]}**
        - Colonnes constantes (1 seule valeur) : **{(summary['Nb valeurs uniques'] <= 1).sum()}**
        """)
        # Bouton de validation de cette étape
        validate_step_button("types")

    # ================================================
    # Onglet 2 — Données manquantes
    # ================================================
    with tabs[1]:
        st.markdown("### 📉 Analyse des valeurs manquantes")
        st.markdown("""
        Visualisez les colonnes ayant des valeurs manquantes :
        - Ajustez un **seuil (%)** pour déterminer quelles colonnes supprimer.
        - Choisissez manuellement ou automatiquement les colonnes à supprimer.
        """)
        # Disposition en deux colonnes pour ajuster le seuil et le nombre d'affichage
        c1, c2 = st.columns(2)
        with c1:
            seuil_pct = st.slider("🎯 Seuil de valeurs manquantes (%)", 0, 100, 20)
        with c2:
            top_n = st.slider("🔢 Colonnes à afficher", 5, 50, 15)
        # Convertit le seuil en proportion (0 à 1)
        seuil = seuil_pct / 100
        # Génère et affiche un graphique interactif des valeurs manquantes
        fig = plot_missing_values(df, seuil=seuil, top_n=top_n)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ Aucune valeur manquante détectée.")
        # Détermine quelles colonnes dépassent le seuil de valeurs manquantes
        cols_to_remove = get_columns_above_threshold(df, seuil)
        if cols_to_remove:
            st.warning(f"{len(cols_to_remove)} colonnes dépassent le seuil de {seuil_pct}%")
            # Permet à l'utilisateur de sélectionner les colonnes à supprimer
            selected = st.multiselect("Colonnes à supprimer", cols_to_remove, default=cols_to_remove)
            if st.button("🗑️ Supprimer sélection", key="drop_missing"):
                df.drop(columns=selected, inplace=True)
                st.session_state.df = df  # Met à jour le DataFrame dans l'état de session
                log_transformation(f"{len(selected)} colonnes supprimées pour valeurs manquantes")
                save_snapshot("missing_dropped")
                st.success("✅ Suppression effectuée.")
        else:
            st.info("Aucune colonne ne dépasse le seuil.")
        # Bouton de validation de l'étape "missing"
        validate_step_button("missing")

    # ================================================
    # Onglet 3 — Distributions
    # ================================================
    with tabs[2]:
        st.markdown("### 📊 Histogrammes")
        st.markdown("Visualisez la distribution d'une variable numérique pour détecter les asymétries, pics ou valeurs extrêmes.")
        # Extraction des colonnes numériques du DataFrame
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if not num_cols:
            st.warning("Aucune variable numérique.")
        else:
            # Permet à l'utilisateur de choisir une variable numérique à visualiser
            col = st.selectbox("Variable à visualiser", num_cols)
            # Crée un histogramme interactif avec Plotly Express
            fig = px.histogram(df, x=col, nbins=50)
            st.plotly_chart(fig, use_container_width=True)
            # Calcule et affiche l'asymétrie de la distribution
            skew = df[col].skew()
            direction = "symétrique" if abs(skew) < 0.5 else (
                "asymétrique positive" if skew > 0 else "asymétrique négative"
            )
            st.markdown(f"**Asymétrie :** `{skew:.2f}` → **{direction}**")
        # Bouton de validation de l'étape "histos"
        validate_step_button("histos")

    # ================================================
    # Onglet 4 — Outliers
    # ================================================
    with tabs[3]:
        st.markdown("### 🚨 Détection des valeurs aberrantes")
        st.markdown("Repérez les outliers à l'aide de la méthode IQR (Interquartile Range).")
        # Permet de sélectionner une variable pour la détection des outliers
        col = st.selectbox("Variable à analyser", num_cols, key="iqr_col")
        # Utilise la fonction dédiée pour détecter les outliers
        outliers = detect_outliers_iqr(df, col)
        st.info(f"{len(outliers)} outliers détectés sur `{col}`")
        st.dataframe(outliers, use_container_width=True)
        # Bouton de validation de l'étape "outliers"
        validate_step_button("outliers")

    # ================================================
    # Onglet 5 — Statistiques descriptives
    # ================================================
    with tabs[4]:
        st.markdown("### 📈 Statistiques descriptives")
        # Calcule et affiche les statistiques descriptives du DataFrame
        stats = df.describe().T
        st.dataframe(stats, use_container_width=True)
        # Estime le pourcentage de valeurs manquantes globales
        n, p = stats.shape[0], df.shape[0]
        pct_missing = 100 - stats["count"].sum() / (n * p) * 100
        st.info(f"{n} variables numériques • Estimation de valeurs manquantes : **{pct_missing:.2f}%**")
        # Bouton de validation de l'étape "stats"
        validate_step_button("stats")

    # ================================================
    # Onglet 6 — Nettoyage automatique
    # ================================================
    with tabs[5]:
        st.markdown("### 🧹 Nettoyage automatique")
        # Détecte et affiche les colonnes constantes
        const_cols = detect_constant_columns(df)
        if const_cols:
            st.warning(f"{len(const_cols)} colonnes constantes détectées")
            if st.button("❌ Supprimer constantes"):
                df.drop(columns=const_cols, inplace=True)
                st.session_state.df = df
                log_transformation(f"Constantes supprimées : {const_cols}")
                save_snapshot("drop_constants")
        # Détecte et affiche les colonnes à faible variance
        low_var = detect_low_variance_columns(df)
        if low_var:
            st.warning(f"{len(low_var)} colonnes à faible variance détectées")
            if st.button("❌ Supprimer faible variance"):
                df.drop(columns=low_var, inplace=True)
                st.session_state.df = df
                log_transformation(f"Faible variance supprimées : {low_var}")
                save_snapshot("drop_low_var")
        # Suppression des doublons : l'utilisateur peut sélectionner les colonnes à utiliser
        st.markdown("#### 🔁 Suppression de doublons")
        sel_cols = st.multiselect("Colonnes à utiliser pour l'identification des doublons", df.columns.tolist())
        dupes = df[df.duplicated(subset=sel_cols or None, keep=False)]
        if not dupes.empty:
            st.warning(f"{len(dupes)} doublons détectés")
            if st.checkbox("Afficher doublons"):
                st.dataframe(dupes)
            if st.button("🗑️ Supprimer doublons"):
                df.drop_duplicates(subset=sel_cols or None, inplace=True)
                st.session_state.df = df
                save_snapshot("drop_duplicates")
                st.success("✅ Doublons supprimés.")
        else:
            st.success("✅ Aucun doublon détecté")
        # Bouton de validation de l'étape "cleaning"
        validate_step_button("cleaning")

    # ================================================
    # Onglet 7 — Corrélations entre variables numériques
    # ================================================
    with tabs[6]:
        st.markdown("### 🔗 Corrélations entre variables numériques")
        st.markdown("""
        Cette matrice permet d’**évaluer les relations linéaires** entre variables numériques.
        - Aide à détecter les redondances (variables fortement corrélées).
        - Met en avant des relations intéressantes pour la modélisation.
        - Les valeurs proches de +1 ou -1 indiquent une forte corrélation.
        """)
        # Sélection de la méthode de corrélation (Pearson, Spearman, Kendall) via radio button
        method = st.radio("📐 Méthode de corrélation :", ["pearson", "spearman", "kendall"], horizontal=True)
        # Récupère les colonnes numériques du DataFrame
        num_cols = df.select_dtypes(include="number").columns
        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour une matrice de corrélation.")
        else:
            # Calcule la matrice de corrélation et l'affiche en utilisant Plotly Express pour une visualisation interactive
            corr = df[num_cols].corr(method=method)
            fig = px.imshow(
                corr,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1
            )
            # Ajuste la taille du graphique en fonction du nombre de variables
            fig.update_layout(
                width=min(1000, 80 * len(num_cols)),
                height=min(1000, 80 * len(num_cols)),
                xaxis=dict(tickangle=45),
                margin=dict(t=40, l=20, r=20, b=80)
            )
            st.plotly_chart(fig, use_container_width=True)
        # Bouton de validation de l'étape "correlations"
        validate_step_button("correlations")

    # -----------------------------------------------
    # Récapitulatif global après nettoyage
    # Affiche un résumé synthétique du DataFrame final à l'aide de summarize_dataframe.
    # -----------------------------------------------
    st.markdown("### 📄 Résumé global (après nettoyage)")
    st.dataframe(summarize_dataframe(df), use_container_width=True)
