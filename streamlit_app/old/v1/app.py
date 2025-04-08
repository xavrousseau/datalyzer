# =============================================================================
# 📦 IMPORTATION DES LIBRAIRIES
# =============================================================================

# Importation de Streamlit : permet de créer des applications web interactives en Python
import streamlit as st  

# Importation de Pandas : fournit des structures de données et des outils d'analyse (DataFrame, etc.)
import pandas as pd  

# Importation de Plotly Express : utilisé pour créer des graphiques interactifs facilement (histogrammes, boxplots, etc.)
import plotly.express as px  

# Importation de fonctions personnalisées pour l'analyse exploratoire (EDA) depuis le fichier eda_utils.py
from eda_utils import (
    detect_variable_types,         # Fonction pour détecter automatiquement le type de chaque colonne (numérique, catégorielle, etc.)
    compute_correlation_matrix,    # Fonction pour calculer la matrice de corrélation entre les variables numériques
    detect_outliers_iqr,           # Fonction pour détecter les valeurs aberrantes (outliers) à l'aide de la méthode IQR (Interquartile Range)
    detect_constant_columns,       # Fonction pour identifier les colonnes ayant une seule valeur (constantes)
    detect_low_variance_columns,   # Fonction pour identifier les colonnes ayant une variance très faible
    encode_categorical,            # Fonction pour encoder les variables catégorielles en utilisant des méthodes comme OneHot ou Ordinal encoding
    plot_missing_values,           # Fonction pour générer un graphique interactif affichant les valeurs manquantes
    get_columns_above_threshold,   # Fonction pour obtenir les colonnes dont le taux de valeurs manquantes dépasse un seuil défini
    drop_missing_columns           # Fonction pour supprimer les colonnes trop incomplètes (taux de valeurs manquantes élevé)
)

# Importation d'une fonction personnalisée pour enregistrer les transformations dans un log
from log_utils import log_transformation  # Permet de suivre et enregistrer les modifications apportées aux données
 

# =============================================================================
# 🎨 CONFIGURATION DE LA PAGE ET STYLE
# =============================================================================

# Configuration de la page Streamlit : titre de l'onglet et mise en page
st.set_page_config(page_title="EDA Explorer", layout="wide")

# Insertion de styles CSS personnalisés pour améliorer l'apparence des composants (boutons, sliders, etc.)
st.markdown("""
    <style>
        /* Personnalisation du style des boutons de Streamlit */
        .stButton>button {
            color: white;
            background: #0099cc;
        }
        /* Personnalisation du style des boutons de téléchargement */
        .stDownloadButton>button {
            background-color: #28a745;
            color: white;
        }
        /* Personnalisation du style des sliders */
        .stSlider>div {
            background-color: #f0f0f5;
        }
    </style>
""", unsafe_allow_html=True)

# Affichage du titre principal de l'application sur la page
st.title("📊 EDA Explorer – Application d'analyse exploratoire de données")
# Séparateur horizontal pour organiser visuellement la page
st.markdown("---")


# =============================================================================
# 1. 📂 CHARGEMENT DU FICHIER CSV
# =============================================================================

# Section d'introduction pour le chargement du fichier
st.markdown("### 📂 1. Chargement du fichier")

# Création d'un composant Streamlit permettant à l'utilisateur de télécharger un fichier CSV depuis son poste
uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])

# Initialisation d'un DataFrame vide qui sera rempli après le chargement du fichier
df = None

# Si un fichier est téléchargé, tenter de le lire et de l'afficher
if uploaded_file is not None:
    try:
        # Lecture du fichier CSV en utilisant Pandas et stockage dans le DataFrame 'df'
        df = pd.read_csv(uploaded_file)

        # Affichage d'un message de succès indiquant que le fichier a été chargé correctement
        st.success("✅ Fichier chargé avec succès.")

        # Création de deux colonnes pour afficher des métriques sur le DataFrame (nombre de lignes et de colonnes)
        col1, col2 = st.columns(2)
        col1.metric("Nombre de lignes", df.shape[0])  # Affiche le nombre de lignes
        col2.metric("Nombre de colonnes", df.shape[1])  # Affiche le nombre de colonnes

        # Affichage des 10 premières lignes du DataFrame pour un aperçu rapide des données
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        # En cas d'erreur lors de la lecture du fichier, afficher un message d'erreur avec le détail
        st.error(f"❌ Erreur lors du chargement du fichier : {e}")


# =============================================================================
# 2. 🔍 ANALYSE EXPLORATOIRE GÉNÉRALE
# =============================================================================

# Si le DataFrame a été correctement chargé, poursuivre avec l'analyse exploratoire
if df is not None:
    st.markdown("### 🔍 2. Analyse exploratoire générale")
    st.markdown("---")

    # SECTION : Détection automatique des types de variables
    # Utilisation d'un expander pour masquer/développer la section d'analyse des types
    with st.expander("📌 Types de variables détectées"):
        st.info("Détection automatique des types : numérique, catégorielle, binaire, texte libre.")
        # Affiche un DataFrame avec les types de variables détectés par la fonction 'detect_variable_types'
        st.dataframe(detect_variable_types(df))

    # Séparation des colonnes numériques et catégorielles pour faciliter l'analyse
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()  # Colonnes numériques
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()  # Colonnes catégorielles

    # Si aucune colonne numérique n'est détectée, afficher une alerte et stopper l'exécution de l'analyse
    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée.")
        st.stop()

    # SECTION : Histogrammes des distributions pour les variables numériques
    with st.expander("📈 Distributions des variables numériques"):
        # Permet à l'utilisateur de sélectionner une variable numérique via un menu déroulant
        col = st.selectbox("Sélectionner une variable", num_cols)
        # Génère et affiche un histogramme interactif avec Plotly Express pour la variable choisie
        st.plotly_chart(px.histogram(df, x=col), use_container_width=True)

    # SECTION : Analyse des valeurs aberrantes (outliers) à l'aide de la méthode IQR
    with st.expander("🚨 Analyse des outliers (IQR)"):
        # Menu déroulant pour choisir la variable numérique à analyser pour les outliers
        col = st.selectbox("Variable numérique à analyser", num_cols, key="iqr_col")
        # Utilise la fonction 'detect_outliers_iqr' pour détecter les outliers dans la variable sélectionnée
        outliers = detect_outliers_iqr(df, col)
        # Affiche le nombre d'outliers détectés
        st.write(f"{len(outliers)} outliers détectés.")
        # Affiche un aperçu des outliers dans un tableau interactif
        st.dataframe(outliers)

    # SECTION : Analyse graphique des valeurs manquantes
    with st.expander("📉 Analyse personnalisée des valeurs manquantes", expanded=True):
        # Création d'un slider pour définir le seuil de valeurs manquantes (en pourcentage)
        seuil_pct = st.slider("🛠️ Définir le seuil (%)", 0, 100, 20)
        seuil = seuil_pct / 100  # Conversion en fraction (0 à 1)
        # Slider pour définir le nombre de colonnes à afficher dans le graphique
        top_n = st.slider("📌 Nombre de colonnes à afficher", 5, 50, 15)

        # Génération du graphique des valeurs manquantes grâce à la fonction 'plot_missing_values'
        fig = plot_missing_values(df, seuil=seuil, top_n=top_n)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ Aucune valeur manquante à visualiser.")

        # Identification des colonnes dont le taux de valeurs manquantes dépasse le seuil défini
        cols_to_remove = get_columns_above_threshold(df, seuil=seuil)
        if cols_to_remove:
            st.warning(f"🚨 {len(cols_to_remove)} colonnes dépassent le seuil de {seuil_pct}%")
            # Affiche la liste des colonnes à supprimer
            st.code(", ".join(cols_to_remove), language="text")

        # Option pour supprimer manuellement les colonnes dépassant le seuil de valeurs manquantes
        if cols_to_remove and st.checkbox("Supprimer ces colonnes"):
            # Suppression des colonnes et récupération de la liste des colonnes supprimées
            df, dropped = drop_missing_columns(df, seuil=seuil)
            # Enregistrement de la transformation dans le log
            log_transformation(f"{len(dropped)} colonnes supprimées pour dépassement du seuil {seuil_pct}%.")
            st.success(f"{len(dropped)} colonnes supprimées.")

    # SECTION : Suggestions automatiques de nettoyage (colonnes constantes, faible variance, valeurs manquantes)
    with st.expander("🧹 Suggestions de nettoyage"):
        st.info("Colonnes potentiellement inutiles à retirer automatiquement.")
        # Affiche les colonnes constantes détectées
        st.write("🔸 Colonnes constantes :", detect_constant_columns(df))
        # Affiche les colonnes à faible variance détectées
        st.write("🔸 Faible variance :", detect_low_variance_columns(df))
        # Calcul et affichage du taux de valeurs manquantes pour chaque colonne, en filtrant celles présentant des valeurs manquantes
        missing = df.isnull().mean().sort_values(ascending=False)
        st.write("🔸 Valeurs manquantes :", missing[missing > 0])

    # SECTION : Nettoyage manuel des données (suppression de doublons et de colonnes sélectionnées)
    with st.expander("🧼 Nettoyage manuel"):
        # Bouton pour supprimer les doublons du DataFrame
        if st.button("🔁 Supprimer les doublons"):
            initial_len = len(df)  # Nombre initial de lignes
            df = df.drop_duplicates()  # Suppression des doublons
            removed = initial_len - len(df)  # Calcul du nombre de doublons supprimés
            log_transformation(f"{removed} doublons supprimés localement.")
            st.success(f"{removed} doublons supprimés.")

        # Permet à l'utilisateur de sélectionner manuellement les colonnes à supprimer via une liste multisélection
        cols_to_drop = st.multiselect("Sélectionner les colonnes à supprimer", df.columns.tolist())
        if cols_to_drop and st.button("🗑️ Supprimer les colonnes sélectionnées"):
            df.drop(columns=cols_to_drop, inplace=True)  # Suppression des colonnes sélectionnées
            log_transformation(f"Colonnes supprimées manuellement : {', '.join(cols_to_drop)}")
            st.success("Colonnes supprimées.")


# =============================================================================
# 3. 🎯 ANALYSE ORIENTÉE VARIABLE CIBLE
# =============================================================================

if df is not None:
    st.markdown("### 🎯 3. Analyse orientée variable cible")
    st.markdown("---")

    # SECTION : Sélection des variables cibles principales et secondaires
    # Permet à l'utilisateur de choisir une variable cible principale parmi les variables numériques
    target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
    # Optionnel : choix d'une seconde variable cible
    target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

    # SECTION : Analyse des corrélations linéaires avec la variable cible principale
    with st.expander("📊 Corrélations avec la cible"):
        st.info("Corrélations linéaires (Pearson).")
        # Calcul de la corrélation de Pearson entre la variable cible et toutes les autres variables numériques
        corr = df.select_dtypes(include=["number"]).corr()[target_1].drop(target_1).sort_values(ascending=False)
        st.dataframe(corr)
        # Affichage d'un graphique en barres des corrélations pour une meilleure visualisation
        st.plotly_chart(px.bar(corr.reset_index(), x="index", y=target_1), use_container_width=True)

    # SECTION : Analyse de la moyenne de la variable cible par groupe (pour une variable catégorielle)
    with st.expander("📈 Graphiques exploratoires métiers"):
        # Sélection d'une variable catégorielle pour regrouper les données
        group_col = st.selectbox("Variable catégorielle", cat_cols, key="groupcol")
        # Calcul de la moyenne de la variable cible principale pour chaque groupe
        avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
        # Affichage du graphique en barres correspondant
        st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

        # Si une variable cible secondaire est sélectionnée, réaliser la même analyse
        if target_2:
            avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

    # SECTION : Encodage des variables catégorielles
    with st.expander("🔄 Encodage des variables catégorielles"):
        # Sélection multiple des colonnes catégorielles à encoder
        selected = st.multiselect("Colonnes à encoder", cat_cols)
        # Choix de la méthode d'encodage (onehot ou ordinal)
        method = st.radio("Méthode", ["onehot", "ordinal"])
        if st.button("Encoder"):
            # Appliquer l'encodage sur une copie du DataFrame pour ne pas altérer l'original
            df_encoded = encode_categorical(df.copy(), method=method, columns=selected)
            st.success(f"{len(selected)} colonnes encodées avec la méthode '{method}'.")
            # Afficher les premières lignes du DataFrame encodé pour vérification
            st.dataframe(df_encoded.head())

    # SECTION : Boxplot interactif pour visualiser la distribution d'une variable numérique selon une catégorisation
    with st.expander("📦 Boxplot interactif"):
        # Choix de la variable catégorielle pour l'axe des X
        cat_col = st.selectbox("X = variable catégorielle", cat_cols, key="box_cat")
        # Choix de la variable numérique pour l'axe des Y
        num_col = st.selectbox("Y = variable numérique", num_cols, key="box_num")
        # Création du boxplot interactif avec Plotly Express
        st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

    # SECTION : Nuage de points (scatter plot) pour analyser la relation entre deux variables numériques
    with st.expander("🧮 Scatter Plot interactif"):
        # Sélection de la variable pour l'axe X
        x = st.selectbox("X", num_cols, key="xscatter")
        # Sélection de la variable pour l'axe Y
        y = st.selectbox("Y", num_cols, key="yscatter")
        # Optionnel : choix d'une variable catégorielle pour colorer les points
        color = st.selectbox("Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
        st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)

    # SECTION : Graphique croisé affichant la moyenne de la variable cible par combinaison de deux variables catégorielles
    with st.expander("🔀 Graphique croisé (moyenne cible)"):
        # Sélection de la première variable catégorielle
        cat1 = st.selectbox("Catégorie X", cat_cols, key="group1")
        # Sélection de la seconde variable catégorielle pour la couleur
        cat2 = st.selectbox("Catégorie couleur", cat_cols, key="group2")
        # Calcul de la moyenne de la variable cible principale par combinaison des deux catégories
        agg_df = (
            df.groupby([cat1, cat2])[target_1]
            .mean()
            .rename("mean_value")
            .reset_index()
        )
        # Création d'un graphique en barres groupées pour visualiser ces moyennes
        fig2d = px.bar(
            agg_df,
            x=cat1,
            y="mean_value",
            color=cat2,
            barmode="group",
            title=f"{target_1} moyen par {cat1} et {cat2}"
        )
        st.plotly_chart(fig2d, use_container_width=True)


# =============================================================================
# 4. 💾 EXPORT DU FICHIER NETTOYÉ
# =============================================================================

if df is not None:
    st.markdown("### 💾 4. Export du fichier final")
    st.markdown("---")

    # SECTION : Exportation du DataFrame nettoyé sous forme de fichier CSV
    with st.expander("💾 Export CSV", expanded=True):
        # Création d'un formulaire Streamlit pour gérer le téléchargement du fichier
        with st.form("export_form"):
            # Champ de texte pour permettre à l'utilisateur de définir le nom du fichier CSV
            file_name = st.text_input("Nom du fichier CSV", value="cleaned_data.csv")
            # Bouton de soumission du formulaire
            submit = st.form_submit_button("📥 Télécharger")
            if submit:
                # Conversion du DataFrame en fichier CSV encodé en UTF-8 (sans index)
                csv = df.to_csv(index=False).encode('utf-8')
                # Création d'un bouton de téléchargement permettant à l'utilisateur de récupérer le fichier CSV
                st.download_button("Télécharger", csv, file_name=file_name, mime="text/csv")



