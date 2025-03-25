# =============================================================================
# IMPORTATION DES LIBRAIRIES
# =============================================================================

# streamlit est une bibliothèque permettant de créer des interfaces web interactives en Python.
# Elle facilite la création d'applications d'analyse de données et de visualisations en quelques lignes.
import streamlit as st

# pandas est une bibliothèque incontournable pour la manipulation et l'analyse de données tabulaires.
import pandas as pd

# requests est utilisé pour effectuer des requêtes HTTP vers une API (ici, pour communiquer avec le backend).
import requests

# plotly.express permet de créer des graphiques interactifs de manière simple.
import plotly.express as px

# os permet d'interagir avec le système de fichiers (par exemple, récupérer des variables d'environnement).
import os


# =============================================================================
# IMPORT DES FONCTIONS D’ANALYSE EDA ET DE LOG
# =============================================================================

# Importation des fonctions d'analyse exploratoire des données (EDA) depuis le module eda_utils.
# Ces fonctions effectuent des tâches telles que la détection de types de variables,
# le calcul de corrélations, la détection d'outliers et la préparation des données pour l'encodage.
from eda_utils import (
    detect_variable_types,      # Détecte automatiquement les types de variables (numériques, catégorielles, etc.)
    compute_correlation_matrix,   # Calcule la matrice de corrélation entre les variables numériques
    detect_outliers_iqr,          # Détecte les outliers à l'aide de la méthode des quartiles (IQR)
    detect_constant_columns,      # Identifie les colonnes ayant des valeurs constantes
    detect_low_variance_columns,  # Identifie les colonnes à faible variance (peu d'information)
    encode_categorical            # Encode les variables catégorielles (méthode onehot ou ordinal)
)

# Importation d'une fonction de log pour enregistrer les transformations effectuées sur le DataFrame.
from log_utils import log_transformation


# =============================================================================
# CONFIGURATION DE L'API BACKEND
# =============================================================================

# Récupère l'URL de l'API backend depuis une variable d'environnement (utile en déploiement)
# Si la variable n'est pas définie, on utilise "http://fastapi:8000" par défaut.
API_URL = os.getenv("API_URL", "http://fastapi:8000")


# =============================================================================
# CONFIGURATION ET INITIALISATION DE LA PAGE STREAMLIT
# =============================================================================

# Configuration de la page Streamlit avec un titre et une mise en page étendue ("wide")
st.set_page_config(page_title="EDA Explorer", layout="wide")

# Affiche le titre principal de l'application dans l'interface web
st.title("📊 EDA Explorer – Application d'analyse exploratoire de données")


# =============================================================================
# 1. CHARGEMENT DU FICHIER CSV
# =============================================================================

# Affiche un en-tête pour la section de chargement du fichier CSV
st.header("1. Charger un fichier CSV")

# Crée un widget permettant à l'utilisateur de sélectionner et uploader un fichier CSV
uploaded_file = st.file_uploader("Choisir un fichier", type=["csv"])

# Initialisation du DataFrame qui contiendra les données uploadées
df = None

# Si un fichier est uploadé, on procède à son traitement
if uploaded_file:
    try:
        # Envoie une requête POST vers l'API backend pour uploader le fichier CSV
        response = requests.post(
            f"{API_URL}/upload/",
            files={"file": (uploaded_file.name, uploaded_file, "text/csv")}
        )

        # Vérifie si l'upload s'est déroulé avec succès (code 200)
        if response.status_code == 200:
            # Récupération des métadonnées retournées par le backend (colonnes, nombre de lignes, etc.)
            meta = response.json()
            st.success("✅ Fichier chargé avec succès.")
            st.write("📌 **Colonnes :**", meta["columns"])
            st.write("📊 **Nombre de lignes :**", meta["rows"])

            # Récupère les 500 premières lignes du fichier pour afficher un aperçu
            head_response = requests.get(f"{API_URL}/head?n=500")
            if head_response.status_code == 200:
                head = head_response.json()
                # Conversion des données JSON en DataFrame pandas
                df = pd.DataFrame(head) if isinstance(head, list) and head else None
            else:
                # Affiche une erreur si l'extraction des données échoue
                st.error("❌ Erreur lors de la récupération des données.")
                st.error(head_response.text)
        else:
            # Affiche une erreur si le backend renvoie un code d'erreur autre que 200
            st.error(f"❌ Erreur serveur : {response.status_code}")
            st.error(response.text)
    except Exception as e:
        # Gestion d'une erreur inattendue lors de l'upload
        st.error(f"❌ Erreur inattendue : {e}")


# =============================================================================
# 2. ANALYSE EXPLORATOIRE GÉNÉRALE (SANS CIBLE)
# =============================================================================

# Si le DataFrame a bien été chargé, on passe à l'analyse exploratoire
if df is not None:
    st.header("2. Analyse exploratoire générale")

    # -------------------------------------------
    # Détection automatique des types de variables
    # -------------------------------------------
    with st.expander("📌 Types de variables détectées", expanded=False):
        st.info("Détection automatique des types : numérique, catégorielle, binaire, texte libre.")
        # Affiche un tableau avec le type de chaque variable, tel que détecté par la fonction dédiée
        st.dataframe(detect_variable_types(df))

    # Récupération des colonnes numériques et catégorielles pour les analyses suivantes
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Si aucune colonne numérique n'est détectée, on arrête l'exécution de l'analyse
    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée.")
        st.stop()

    # -------------------------------------------
    # Histogrammes des variables numériques
    # -------------------------------------------
    with st.expander("📈 Distributions des variables numériques", expanded=False):
        st.info("Histogrammes des variables numériques.")
        # Permet à l'utilisateur de sélectionner une variable numérique pour afficher son histogramme
        col = st.selectbox("Sélectionner une variable", num_cols)
        st.plotly_chart(px.histogram(df, x=col), use_container_width=True)

    # -------------------------------------------
    # Analyse des outliers via la méthode IQR
    # -------------------------------------------
    with st.expander("🚨 Analyse des outliers (IQR)", expanded=False):
        st.info("Méthode des quartiles (IQR).")
        # Sélection de la variable numérique à analyser pour la détection d'outliers
        col = st.selectbox("Variable numérique à analyser", num_cols, key="iqr_col")
        # Détection des outliers à l'aide de la fonction dédiée
        outliers = detect_outliers_iqr(df, col)
        st.write(f"{len(outliers)} outliers détectés.")
        # Affichage des outliers dans un tableau
        st.dataframe(outliers)

    # -------------------------------------------
    # Suggestions automatiques de nettoyage des données
    # -------------------------------------------
    with st.expander("🧹 Suggestions de nettoyage", expanded=False):
        st.info("Détection automatique : constantes, faible variance, valeurs manquantes.")
        st.write("Colonnes constantes :", detect_constant_columns(df))
        st.write("Colonnes à faible variance :", detect_low_variance_columns(df))
        # Calcul et affichage du pourcentage de valeurs manquantes par colonne
        missing = df.isnull().mean().sort_values(ascending=False)
        st.write("Valeurs manquantes :", missing[missing > 0])

    # -------------------------------------------
    # Nettoyage manuel des données
    # -------------------------------------------
    with st.expander("🧼 Nettoyage manuel", expanded=False):
        # Bouton pour supprimer les doublons via l'API backend
        if st.button("Supprimer les doublons"):
            res = requests.post(f"{API_URL}/drop-duplicates/").json()
            st.success(f"{res['removed']} doublons supprimés.")
            # Mise à jour locale du DataFrame après suppression des doublons
            updated = requests.get(f"{API_URL}/head?n=500").json()
            df = pd.DataFrame(updated)

        # Permet à l'utilisateur de sélectionner des colonnes à supprimer manuellement
        cols_to_drop = st.multiselect("Colonnes à supprimer", df.columns.tolist())
        if cols_to_drop and st.button("Supprimer les colonnes sélectionnées"):
            res = requests.post(f"{API_URL}/drop-columns/", json={"columns": cols_to_drop})
            st.success(res.json()["message"])
            # Mise à jour locale du DataFrame après suppression des colonnes
            updated = requests.get(f"{API_URL}/head?n=500").json()
            df = pd.DataFrame(updated)


# =============================================================================
# 3. ANALYSE ORIENTÉE VARIABLE CIBLE
# =============================================================================

# Cette section permet de guider l'analyse en se focalisant sur une ou deux variables cibles
if df is not None:
    st.header("3. Analyse orientée variable cible")
    st.markdown("Définissez une ou deux variables cibles numériques pour guider l’analyse.")

    # Sélection des variables cibles principales et secondaires dans les colonnes numériques
    target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
    target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

    # -------------------------------------------
    # Analyse de la corrélation entre les variables et la cible principale
    # -------------------------------------------
    with st.expander("📊 Corrélations avec la cible", expanded=False):
        st.info("Analyse des corrélations linéaires (Pearson).")
        # Calcul de la corrélation entre la cible principale et toutes les autres variables numériques
        corr = df.select_dtypes(include=["number"]).corr()[target_1].drop(target_1).sort_values(ascending=False)
        st.dataframe(corr)
        # Visualisation de la corrélation sous forme de graphique à barres
        st.plotly_chart(px.bar(corr.reset_index(), x="index", y=target_1), use_container_width=True)

    # -------------------------------------------
    # Graphiques exploratoires métiers basés sur une variable catégorielle
    # -------------------------------------------
    with st.expander("📈 Graphiques exploratoires métiers", expanded=False):
        # Sélection d'une variable catégorielle pour le groupement
        group_col = st.selectbox("Variable catégorielle", cat_cols, key="groupcol")
        st.info("Bar chart de la moyenne de la cible par groupe.")

        # Calcul et affichage de la moyenne de la cible principale par groupe
        avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
        st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

        # Si une seconde cible est sélectionnée, affiche également la moyenne correspondante par groupe
        if target_2:
            avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

    # -------------------------------------------
    # Encodage des variables catégorielles
    # -------------------------------------------
    with st.expander("🔄 Encodage des variables catégorielles", expanded=False):
        st.info("OneHot ou Ordinal Encoding.")
        # Permet à l'utilisateur de sélectionner les colonnes catégorielles à encoder
        selected = st.multiselect("Colonnes à encoder", cat_cols)
        # Choix de la méthode d'encodage entre onehot et ordinal
        method = st.radio("Méthode", ["onehot", "ordinal"])
        if st.button("Encoder"):
            # Applique l'encodage sur une copie du DataFrame
            df_encoded = encode_categorical(df.copy(), method=method, columns=selected)
            st.success(f"{len(selected)} colonnes encodées avec la méthode '{method}'.")
            st.dataframe(df_encoded.head())

    # -------------------------------------------
    # Visualisation avec un boxplot interactif
    # -------------------------------------------
    with st.expander("📦 Boxplot interactif", expanded=False):
        st.info("Visualise la dispersion selon une catégorie.")
        # Sélection d'une variable catégorielle pour l'axe X et d'une variable numérique pour l'axe Y
        cat_col = st.selectbox("X = variable catégorielle", cat_cols, key="box_cat")
        num_col = st.selectbox("Y = variable numérique", num_cols, key="box_num")
        st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

    # -------------------------------------------
    # Visualisation avec un scatter plot interactif
    # -------------------------------------------
    with st.expander("🧮 Scatter Plot interactif", expanded=False):
        st.info("Nuage de points entre deux variables numériques.")
        # Sélection des variables numériques pour les axes X et Y, et optionnellement une variable pour la couleur
        x = st.selectbox("X", num_cols, key="xscatter")
        y = st.selectbox("Y", num_cols, key="yscatter")
        color = st.selectbox("Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
        st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)

    # -------------------------------------------
    # Visualisation avec un graphique croisé (bar chart groupé)
    # -------------------------------------------
    with st.expander("🔀 Graphique croisé (moyenne cible)", expanded=False):
        st.info("Analyse croisée par deux variables catégorielles.")
        # Sélection de deux variables catégorielles pour analyser la moyenne de la cible principale
        cat1 = st.selectbox("Catégorie X", cat_cols, key="group1")
        cat2 = st.selectbox("Catégorie couleur", cat_cols, key="group2")
        agg_df = df.groupby([cat1, cat2])[target_1].mean().reset_index()
        st.plotly_chart(px.bar(agg_df, x=cat1, y=target_1, color=cat2, barmode="group"), use_container_width=True)


# =============================================================================
# 4. EXPORT FINAL
# =============================================================================

# Cette section permet d'exporter les résultats finaux (rapport, sauvegarde du DataFrame, CSV nettoyé)
if df is not None:
    st.header("4. Export du fichier final")

    # -------------------------------------------
    # Génération d'un rapport HTML avec profiling automatique
    # -------------------------------------------
    with st.expander("📄 Rapport HTML (profiling)", expanded=False):
        st.info("Profiling automatique du jeu de données.")
        if st.button("Générer le rapport"):
            # Importation de ydata_profiling pour générer un rapport détaillé du DataFrame
            from ydata_profiling import ProfileReport
            # Création du répertoire d'export si nécessaire
            os.makedirs("data/exports", exist_ok=True)
            # Génération du rapport de profiling
            profile = ProfileReport(df, title="Rapport EDA", explorative=True)
            profile.to_file("data/exports/eda_report.html")
            # Propose un bouton de téléchargement pour le rapport HTML généré
            with open("data/exports/eda_report.html", "rb") as f:
                st.download_button("Télécharger le rapport", f, file_name="eda_report.html")

    # -------------------------------------------
    # Sauvegarde du DataFrame au format Parquet avec enregistrement dans le log
    # -------------------------------------------
    with st.expander("💾 Sauvegarder avec log", expanded=False):
        st.info("Sauvegarde Parquet avec trace des actions.")
        if st.button("Sauvegarder maintenant"):
            os.makedirs("data/exports", exist_ok=True)
            path = "data/exports/final_dataframe.parquet"
            df.to_parquet(path)
            log_transformation(f"DataFrame sauvegardé à {path} avec {df.shape[0]} lignes et {df.shape[1]} colonnes.")
            st.success("Sauvegarde et log OK ✅")

    # -------------------------------------------
    # Export du DataFrame nettoyé sous format CSV
    # -------------------------------------------
    if st.button("📤 Exporter le CSV nettoyé"):
        r = requests.get(f"{API_URL}/export/")
        if r.status_code == 200:
            st.download_button("Télécharger le CSV", r.content, file_name="cleaned_data.csv")
        else:
            st.error("Erreur lors de l'export du CSV.")
