# =============================================================================
# 📦 IMPORTATION DES LIBRAIRIES
# =============================================================================

import streamlit as st       # Pour créer l'application web interactive
import pandas as pd          # Pour la manipulation de données
import plotly.express as px  # Pour les visualisations interactives
import numpy as np
from scipy.stats import zscore
import csv                   # Pour la détection du séparateur dans les CSV/TXT
from io import StringIO, BytesIO  # Pour manipuler les flux de données

import sys                   # Pour les interactions système (ex: monitoring)
import psutil                # Pour l'analyse de la mémoire

# Importation des fonctions utilitaires pour l'EDA
from eda_utils import (
    detect_variable_types,         # Détecte les types de variables
    compute_correlation_matrix,    # Calcule la matrice de corrélation
    detect_outliers_iqr,           # Détecte les outliers via la méthode IQR
    detect_constant_columns,       # Détecte les colonnes constantes
    detect_low_variance_columns,   # Détecte les colonnes à faible variance
    encode_categorical,            # Encodage des variables catégorielles (OneHot ou Ordinal)
    plot_missing_values,           # Trace le graphique des valeurs manquantes
    get_columns_above_threshold,   # Liste les colonnes avec un taux de NA supérieur au seuil
    drop_missing_columns           # Supprime les colonnes trop incomplètes
)

# Importation d'une fonction pour enregistrer les transformations appliquées
from log_utils import log_transformation

# =============================================================================
# 🎨 CONFIGURATION GLOBALE DE L’APP
# =============================================================================

st.set_page_config(
    page_title="EDA Explorer – Analyse exploratoire de données",
    layout="wide"
)

# Insertion de styles CSS personnalisés pour les éléments de l'application
st.markdown("""
    <style>
        .stButton>button {
            color: white;
            background: #0099cc;
        }
        .stDownloadButton>button {
            background-color: #28a745;
            color: white;
        }
        .stSlider>div {
            background-color: #f0f0f5;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 🧭 BARRE DE NAVIGATION
# =============================================================================

# Menu latéral pour naviguer entre les sections de l'application
section = st.sidebar.radio("🧭 Navigation", [
    "📂 Chargement",
    "🔍 Analyse exploratoire",
    "📊 Analyse catégorielle",
    "🎯 Analyse variable cible",
    "💾 Export"
])

# Initialisation des variables globales : le DataFrame et le fichier uploadé
# Affiche un avertissement global si aucun fichier n'est chargé
uploaded_file = st.session_state.get("uploaded_file")

if section != "📂 Chargement" and uploaded_file is None:
    st.warning("📂 Veuillez d’abord charger un fichier via la section '📂 Chargement'.")
    st.stop()
# =============================================================================
# 📂 1. Chargement du fichier (Accueil)
# =============================================================================

if section == "📂 Chargement":
    st.title("📊 EDA Explorer – Application d'analyse exploratoire de données")
    st.markdown("---")

    st.subheader("📂 Chargement du fichier")
    st.info("📦 Vous pouvez importer un fichier jusqu’à **200 Mo** (formats supportés : CSV, TXT, JSON, XLSX, Parquet).")

    # Composant d’upload
    uploaded_file = st.file_uploader("Choisissez un fichier", type=["csv", "txt", "json", "xlsx", "parquet"])

    if uploaded_file:
        # Sauvegarde du fichier uploadé dans la session pour les prochaines sections
        st.session_state["uploaded_file"] = uploaded_file
        file_extension = uploaded_file.name.split(".")[-1].lower()
        st.info(f"📄 Fichier sélectionné : `{uploaded_file.name}`")

        try:
            # Pour éviter les problèmes liés à la position du curseur, on se replace au début
            uploaded_file.seek(0)
            if file_extension in ["csv", "txt"]:
                raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
                # Détection automatique du séparateur grâce à csv.Sniffer
                detected_sep = csv.Sniffer().sniff(raw_text[:2048]).delimiter
                st.success(f"✅ Séparateur détecté automatiquement : `{detected_sep}`")
                df = pd.read_csv(StringIO(raw_text), sep=detected_sep)

            elif file_extension == "json":
                uploaded_file.seek(0)
                df = pd.read_json(uploaded_file)

            elif file_extension == "xlsx":
                df = pd.read_excel(uploaded_file)

            elif file_extension == "parquet":
                df = pd.read_parquet(uploaded_file)

        except Exception as e:
            st.error(f"❌ Erreur de lecture : {e}")

        # Aperçu si tout s’est bien passé
        if df is not None:
            st.success("✅ Fichier chargé avec succès.")
            # Sauvegarde du DataFrame dans la session pour éviter de le recharger
            st.session_state.df = df
            max_rows = st.radio("Nombre de lignes à afficher :", [5, 10, 20, 50, 100], horizontal=True)
            col1, col2 = st.columns(2)
            col1.metric("Lignes", f"{df.shape[0]:,}".replace(",", " "))
            col2.metric("Colonnes", f"{df.shape[1]:,}".replace(",", " "))
            st.dataframe(df.head(max_rows), use_container_width=True)

# =============================================================================
# 🔍 2. Analyse exploratoire (EDA)
# =============================================================================

elif section == "🔍 Analyse exploratoire" and uploaded_file:
    # Récupération du DataFrame depuis la session si déjà chargé,
    # sinon on le recharge à partir du fichier uploadé.
    if "df" not in st.session_state:
        uploaded_file.seek(0)  # Remise à zéro du curseur pour une lecture correcte
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension in ["csv", "txt"]:
            raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
            sep = csv.Sniffer().sniff(raw_text[:2048]).delimiter
            df = pd.read_csv(StringIO(raw_text), sep=sep)
        elif file_extension == "json":
            uploaded_file.seek(0)
            df = pd.read_json(uploaded_file)
        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file)
        elif file_extension == "parquet":
            df = pd.read_parquet(uploaded_file)
        st.session_state.df = df
    else:
        df = st.session_state.df

    st.subheader("🔍 Analyse exploratoire")
    # Création des onglets pour organiser les analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📌 Types de variables",
        "📉 Valeurs manquantes",
        "📈 Histogrammes",
        "🚨 Outliers",
        "🧹 Nettoyage auto",
        "🧼 Nettoyage manuel",
        "📐 Stats descriptives",
        "🧬 Corrélations avancées"
    ])
    # -------------------------------------------------------------------------
    # Onglet 1 : Types de variables
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📌 Types de variables détectées")
        st.info("Aperçu des colonnes avec type détecté, nombre de valeurs uniques, valeurs manquantes et exemple.")
        summary = pd.DataFrame({
            "Nom de la colonne": df.columns,
            "Type pandas": df.dtypes.astype(str),
            "Nb valeurs uniques": df.nunique(),
            "% valeurs manquantes": (df.isna().mean() * 100).round(1).astype(str) + " %",
            "Exemple de valeur": [
                df[col].dropna().astype(str).unique()[0] if df[col].dropna().shape[0] > 0 else "—"
                for col in df.columns
            ]
        }).sort_values("Type pandas")
        st.dataframe(summary, use_container_width=True, height=500)

    # -------------------------------------------------------------------------
    # Onglet 2 : Valeurs manquantes
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 📉 Analyse des valeurs manquantes")
        seuil_pct = st.slider("🛠️ Seuil (%) de valeurs manquantes", 0, 100, 20)
        seuil = seuil_pct / 100
        top_n = st.slider("📌 Top colonnes à afficher", 5, 50, 15)

        fig = plot_missing_values(df, seuil=seuil, top_n=top_n)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ Aucune valeur manquante.")

        cols_to_remove = get_columns_above_threshold(df, seuil=seuil)
        if cols_to_remove:
            st.warning(f"{len(cols_to_remove)} colonnes dépassent {seuil_pct}% de valeurs manquantes.")
            st.code(", ".join(cols_to_remove))

            if st.checkbox("❌ Supprimer ces colonnes"):
                df, dropped = drop_missing_columns(df, seuil=seuil)
                log_transformation(f"{len(dropped)} colonnes supprimées pour seuil {seuil_pct}%")
                st.success(f"{len(dropped)} colonnes supprimées.")
                st.session_state.df = df

    # -------------------------------------------------------------------------
    # Onglet 3 : Histogrammes des variables numériques
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### 📈 Distribution des variables numériques")
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            selected_num = st.selectbox("📊 Choisissez une variable", num_cols)
            st.plotly_chart(px.histogram(df, x=selected_num), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 4 : Détection d'outliers (méthode IQR)
    # -------------------------------------------------------------------------
    with tab4:
        st.markdown("### 🚨 Détection d'outliers (méthode IQR)")
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        col = st.selectbox("Variable à analyser", num_cols, key="iqr_col")
        outliers = detect_outliers_iqr(df, col)
        st.write(f"🔍 {len(outliers)} outliers détectés.")
        st.dataframe(outliers)

    # -------------------------------------------------------------------------
    # Onglet 5 : Suggestions automatiques de nettoyage
    # -------------------------------------------------------------------------
    with tab5:
        st.markdown("### 🧹 Suggestions automatiques de nettoyage")
        st.info("Colonnes constantes, faible variance ou fortement manquantes.")
        st.write("🔸 Colonnes constantes :", detect_constant_columns(df))
        st.write("🔸 Faible variance :", detect_low_variance_columns(df))
        missing = df.isnull().mean().sort_values(ascending=False)
        st.write("🔸 Valeurs manquantes :", missing[missing > 0])

    # -------------------------------------------------------------------------
    # Onglet 6 : Nettoyage manuel
    # -------------------------------------------------------------------------
    with tab6:
        st.markdown("### 🧼 Nettoyage manuel")
        if st.button("🔁 Supprimer les doublons"):
            initial_len = len(df)
            df = df.drop_duplicates()
            removed = initial_len - len(df)
            st.session_state.df = df
            log_transformation(f"{removed} doublons supprimés.")
            st.success(f"{removed} doublons supprimés.")

        cols_to_drop = st.multiselect("Colonnes à supprimer", df.columns.tolist())
        if cols_to_drop and st.button("🗑️ Supprimer les colonnes sélectionnées"):
            df.drop(columns=cols_to_drop, inplace=True)
            log_transformation(f"Colonnes supprimées manuellement : {', '.join(cols_to_drop)}")
            st.session_state.df = df
            st.success("Colonnes supprimées.")

    # -------------------------------------------------------------------------
    # Onglet 7 : Statistiques descriptives avancées
    # -------------------------------------------------------------------------
    with tab7:
        st.markdown("### 📐 Statistiques descriptives avancées")

        st.info("Affiche les statistiques classiques (moyenne, écart-type…) et avancées (skewness, kurtosis).")

        # Colonnes numériques détectées automatiquement
        num_cols = df.select_dtypes(include="number").columns.tolist()

        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
            st.stop()

        # Option : analyse groupée par une variable catégorielle
        group_by = st.selectbox("🔁 Grouper par (optionnel)", [None] + df.select_dtypes(include=["object", "category"]).columns.tolist())

        if group_by:
            # Calcul des statistiques groupées
            desc_stats = df.groupby(group_by)[num_cols].agg(["mean", "median", "std", "min", "max", "skew", "kurt"])
            # Aplatir les colonnes multi-index
            desc_stats.columns = ['_'.join(col).strip() for col in desc_stats.columns.values]
            st.dataframe(desc_stats, use_container_width=True)
        else:
            # Statistiques globales sur les colonnes numériques
            desc_stats = df[num_cols].agg(["mean", "median", "std", "min", "max", "skew", "kurt"]).T
            desc_stats.columns = ["Moyenne", "Médiane", "Écart-type", "Min", "Max", "Skewness", "Kurtosis"]
            st.dataframe(desc_stats, use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 8 : Corrélation avancée
    # -------------------------------------------------------------------------
    with tab8:
        st.markdown("### 🧬 Corrélation avancée entre variables numériques")
        st.info("📌 Analyse des dépendances linéaires et non-linéaires entre variables numériques.")

        # Sélection du type de corrélation à afficher
        method = st.radio("📐 Méthode de corrélation :", ["pearson", "spearman", "kendall"], horizontal=True)

        # Slider pour appliquer un seuil minimal d'affichage
        threshold = st.slider("🎚️ Seuil de corrélation absolue minimale", 0.0, 1.0, 0.3, 0.05)

        # Sélection des colonnes numériques uniquement
        numeric_cols = df.select_dtypes(include=["number"]).columns

        if len(numeric_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour afficher une matrice de corrélation.")
        else:
            # Calcul de la matrice de corrélation avec la méthode choisie
            corr_matrix = df[numeric_cols].corr(method=method)

            # Création d'une version aplatie de la matrice (utile pour filtrer)
            corr_pairs = (
                corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                .stack()
                .reset_index()
            )
            corr_pairs.columns = ["Variable 1", "Variable 2", "Corrélation"]

            # Filtrage selon le seuil choisi
            filtered_corr = corr_pairs[abs(corr_pairs["Corrélation"]) >= threshold]
            filtered_corr = filtered_corr.sort_values("Corrélation", ascending=False)

            st.markdown("#### 📋 Paires de variables corrélées")
            st.dataframe(filtered_corr, use_container_width=True)

            # Heatmap interactive (optionnelle)
            st.markdown("#### 🌡️ Heatmap de la matrice de corrélation")
            fig = px.imshow(
                corr_matrix,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto",
                title=f"Matrice de corrélation ({method})"
            )
            st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 📊 3. Analyse des variables catégorielles
# =============================================================================

elif section == "📊 Analyse catégorielle" and uploaded_file:
    # Chargement du DataFrame
    if "df" not in st.session_state:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
    else:
        df = st.session_state.df

    st.subheader("📊 Analyse des variables catégorielles")

    # Détection automatique des colonnes catégorielles
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not cat_cols:
        st.warning("⚠️ Aucune variable catégorielle détectée dans le dataset.")
        st.stop()

    # Création des onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Aperçu global",
        "📊 Barplots",
        "📈 Fréquences cumulées",
        "💡 Suggestions d'encodage"
    ])

    # -------------------------------------------------------------------------
    # Onglet 1 : Aperçu global des colonnes catégorielles
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📋 Détail des variables catégorielles")
        st.info("Nombre de modalités uniques, modalité la plus fréquente et taux de valeurs manquantes.")

        summary_cat = pd.DataFrame({
            "Colonne": cat_cols,
            "Nb modalités uniques": [df[col].nunique() for col in cat_cols],
            "Modalité la + fréquente": [df[col].mode()[0] if not df[col].mode().empty else "—" for col in cat_cols],
            "Valeurs manquantes (%)": [f"{df[col].isna().mean() * 100:.1f} %" for col in cat_cols]
        })

        st.dataframe(summary_cat, use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 2 : Barplots des top modalités
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 📊 Distribution des modalités (Top N)")
        selected_col = st.selectbox("📌 Choisissez une variable catégorielle", cat_cols, key="cat_barplot")
        top_n = st.slider("🔢 Nombre de modalités à afficher", 3, 30, 10)

        top_modalities = (
            df[selected_col]
            .value_counts()
            .head(top_n)
            .reset_index()
        )
        top_modalities.columns = ["Modalité", "Fréquence"]

        fig = px.bar(
            top_modalities,
            x="Modalité",
            y="Fréquence",
            title=f"Top {top_n} modalités – {selected_col}",
            text="Fréquence"
        )
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 3 : Fréquences relatives et cumulées
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### 📈 Fréquences relatives et cumulées")
        selected_col = st.selectbox("📊 Variable catégorielle à analyser", cat_cols, key="cat_freq")

        # Calcul des fréquences relatives
        freq_df = df[selected_col].value_counts(normalize=True).reset_index()

        # Renommage des colonnes pour correspondre à celles appelées ensuite
        freq_df.columns = ["Modalité", "Fréquence"]

        # Calcul des fréquences cumulées
        freq_df["Fréquence cumulée"] = freq_df["Fréquence"].cumsum()
        freq_df["% Fréquence"] = (freq_df["Fréquence"] * 100).round(2).astype(str) + " %"
        freq_df["% Cumulée"] = (freq_df["Fréquence cumulée"] * 100).round(2).astype(str) + " %"

        # Affichage du tableau final avec les bonnes colonnes
        st.dataframe(freq_df[["Modalité", "% Fréquence", "% Cumulée"]], use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 4 : Suggestions d’encodage selon la cardinalité
    # -------------------------------------------------------------------------
    with tab4:
        st.markdown("### 💡 Suggestions d'encodage automatique")
        st.info("Encodage recommandé en fonction du nombre de modalités uniques par colonne.")

        seuil_card = st.slider("🔧 Seuil max pour OneHot encoding (nb modalités)", 2, 50, 10)

        suggestions = []
        for col in cat_cols:
            nb_modal = df[col].nunique()
            if nb_modal <= seuil_card:
                suggestion = "OneHot"
            elif nb_modal == 2:
                suggestion = "Binaire"
            elif nb_modal > seuil_card:
                suggestion = "Ordinal / Embedding"
            else:
                suggestion = "À vérifier"

            suggestions.append((col, nb_modal, suggestion))

        suggestion_df = pd.DataFrame(suggestions, columns=["Colonne", "Nb modalités", "Encodage suggéré"])
        st.dataframe(suggestion_df.sort_values("Nb modalités"), use_container_width=True)

# =============================================================================
# 🚨 4. Détection de problèmes de qualité de données
# =============================================================================

elif section == "🚨 Qualité des données" and uploaded_file:
    if "df" not in st.session_state:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
    else:
        df = st.session_state.df

    st.subheader("🚨 Problèmes potentiels de qualité des données")

    # -------------------------------------------------------------------------
    st.markdown("### 🔍 Colonnes mal typées")
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object")
        if df[col].str.replace(".", "", regex=False).str.replace(",", "", regex=False).str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning(f"📌 Ces colonnes semblent contenir des valeurs numériques mais sont typées comme 'object' :")
        st.code(", ".join(suspect_numeric_as_str))
    else:
        st.success("✅ Aucun champ suspect détecté parmi les variables 'object'.")

    # -------------------------------------------------------------------------
    st.markdown("### 📛 Noms suspects ou non normalisés")
    suspect_names = [col for col in df.columns if col.startswith("Unnamed") or "id" in col.lower()]
    if suspect_names:
        st.warning("⚠️ Colonnes avec noms suspects :")
        st.code(", ".join(suspect_names))
    else:
        st.success("✅ Aucun nom de colonne suspect détecté.")

    # -------------------------------------------------------------------------
    st.markdown("### 🧩 Valeurs suspectes ou placeholders")
    placeholder_values = ["unknown", "n/a", "na", "undefined", "None", "missing", "?"]
    placeholder_hits = {}
    for col in df.columns:
        hits = df[col].astype(str).str.lower().isin(placeholder_values).sum()
        if hits > 0:
            placeholder_hits[col] = hits
    if placeholder_hits:
        st.warning("🔍 Valeurs suspectes trouvées (placeholders) :")
        st.write(pd.DataFrame.from_dict(placeholder_hits, orient="index", columns=["Occurrences"]))
    else:
        st.success("✅ Aucune valeur placeholder détectée.")

    # -------------------------------------------------------------------------
    st.markdown("### 🧪 Valeurs extrêmes (Z-score simplifié)")
    import numpy as np
    from scipy.stats import zscore

    num_cols = df.select_dtypes(include="number").columns
    z_outlier_summary = {}
    for col in num_cols:
        if df[col].dropna().std() == 0:
            continue
        z_scores = np.abs(zscore(df[col].dropna()))
        outliers = (z_scores > 3).sum()
        if outliers > 0:
            z_outlier_summary[col] = outliers
    if z_outlier_summary:
        st.warning("🚨 Valeurs extrêmes détectées (Z-score > 3) :")
        st.write(pd.DataFrame.from_dict(z_outlier_summary, orient="index", columns=["Nb outliers"]))
    else:
        st.success("✅ Pas de valeurs extrêmes détectées via Z-score.")

    # -------------------------------------------------------------------------
    st.markdown("### 📌 Colonnes uniques / constantes")
    const_cols = detect_constant_columns(df)
    if const_cols:
        st.warning(f"⚠️ Colonnes constantes détectées ({len(const_cols)}) :")
        st.code(", ".join(const_cols))
    else:
        st.success("✅ Aucune colonne constante détectée.")

# =============================================================================
# 🧪 5. Analyse multivariée et interactions
# =============================================================================

elif section == "🧪 Analyse multivariée" and uploaded_file:
    if "df" not in st.session_state:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
    else:
        df = st.session_state.df

    st.subheader("🧪 Analyse multivariée et interactions")

    # Séparation des types de variables
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    tab1, tab2, tab3 = st.tabs([
        "📉 ACP (PCA)",
        "📊 Interactions num ↔ cat",
        "📚 Corrélation catégorielle"
    ])

    # -------------------------------------------------------------------------
    # Onglet 1 – ACP sur les variables numériques
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📉 Analyse en Composantes Principales (ACP / PCA)")
        st.info("Permet de réduire les dimensions tout en conservant un maximum d'information.")

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour l'ACP.")
        else:
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA
            import plotly.express as px

            df_scaled = StandardScaler().fit_transform(df[num_cols].dropna())

            n_comp = st.slider("Nombre de composantes", 2, min(10, len(num_cols)), 2)
            pca = PCA(n_components=n_comp)
            components = pca.fit_transform(df_scaled)

            pca_df = pd.DataFrame(components, columns=[f"PC{i+1}" for i in range(n_comp)])

            # Option de colorisation par catégorie
            color_cat = st.selectbox("Colorer par (optionnel)", [None] + cat_cols)
            if color_cat:
                pca_df[color_cat] = df[cat_cols][color_cat]

            # Graphique 2D
            st.markdown("#### 🌈 Projection des données (PC1 vs PC2)")
            fig = px.scatter(pca_df, x="PC1", y="PC2", color=color_cat if color_cat else None)
            st.plotly_chart(fig, use_container_width=True)

            # Variance expliquée
            explained = pd.DataFrame({
                "Composante": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
                "Variance expliquée (%)": (pca.explained_variance_ratio_ * 100).round(2)
            })
            st.markdown("#### 📈 Variance expliquée par composante")
            st.dataframe(explained)

    # -------------------------------------------------------------------------
    # Onglet 2 – Num ↔ Cat : boxplot et swarmplot
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 🧮 Analyse croisée numérique / catégorielle")

        if not cat_cols or not num_cols:
            st.warning("⚠️ Il faut au moins une variable catégorielle et une numérique.")
        else:
            cat_var = st.selectbox("Variable catégorielle", cat_cols, key="cat_group")
            num_var = st.selectbox("Variable numérique", num_cols, key="num_group")

            st.plotly_chart(px.box(df, x=cat_var, y=num_var, title="Boxplot croisé"), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 3 – Corrélations entre variables catégorielles
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### 📚 Corrélations entre variables catégorielles (Cramér's V)")
        st.info("Mesure la force de l'association entre deux variables catégorielles.")

        if len(cat_cols) < 2:
            st.warning("⚠️ Pas assez de colonnes catégorielles pour le calcul de Cramér's V.")
        else:
            import numpy as np
            import seaborn as sns
            import matplotlib.pyplot as plt
            from scipy.stats import chi2_contingency

            def cramers_v(x, y):
                confusion_matrix = pd.crosstab(x, y)
                chi2 = chi2_contingency(confusion_matrix)[0]
                n = confusion_matrix.sum().sum()
                phi2 = chi2 / n
                r, k = confusion_matrix.shape
                phi2corr = max(0, phi2 - ((k-1)*(r-1)) / (n-1))
                rcorr = r - ((r-1)**2)/(n-1)
                kcorr = k - ((k-1)**2)/(n-1)
                return np.sqrt(phi2corr / min((kcorr-1), (rcorr-1)))

            matrix = pd.DataFrame(index=cat_cols, columns=cat_cols)
            for col1 in cat_cols:
                for col2 in cat_cols:
                    if col1 == col2:
                        matrix.loc[col1, col2] = 1.0
                    else:
                        matrix.loc[col1, col2] = cramers_v(df[col1], df[col2])
            matrix = matrix.astype(float)

            st.markdown("#### 🔥 Matrice de Cramér's V")
            fig = px.imshow(matrix, text_auto=".2f", aspect="auto", color_continuous_scale="OrRd")
            st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 🎯 6. Analyse orientée cible
# =============================================================================

elif section == "🎯 Analyse variable cible" and uploaded_file:
    # On récupère le DataFrame nettoyé depuis la session s'il existe, sinon on le recharge.
    if "df" not in st.session_state:
        # ATTENTION : ici, le chargement est simplifié pour un fichier CSV.
        # Pour d'autres formats, il faut adapter la lecture (cf. section Chargement).
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
    else:
        df = st.session_state.df

    st.subheader("🎯 Analyse orientée variable cible")

    # Détection des variables numériques et catégorielles
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée.")
        st.stop()

    # Sélection de la variable cible principale et optionnelle
    target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
    target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

    # Création des onglets pour l'analyse de la variable cible
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Corrélations",
        "📈 Cible par groupe",
        "📦 Boxplot",
        "🧮 Nuage de points"
    ])

    # -------------------------------------------------------------------------
    # Onglet 1 : Corrélations
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📊 Corrélations avec la variable cible")
        st.info("Corrélations linéaires (Pearson) avec la variable cible principale.")
        corr = df.select_dtypes(include=["number"]).corr()[target_1].drop(target_1).sort_values(ascending=False)
        st.dataframe(corr)
        st.plotly_chart(px.bar(corr.reset_index(), x="index", y=target_1), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 2 : Analyse de la cible par groupe
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 📈 Moyenne de la cible par groupe")
        group_col = st.selectbox("Variable catégorielle", cat_cols, key="groupcol")
        avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
        st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

        if target_2:
            avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 3 : Boxplot interactif
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### 📦 Boxplot interactif")
        cat_col = st.selectbox("X = variable catégorielle", cat_cols, key="box_cat")
        num_col = st.selectbox("Y = variable numérique", num_cols, key="box_num")
        st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 4 : Scatter Plot (nuage de points)
    # -------------------------------------------------------------------------
    with tab4:
        st.markdown("### 🧮 Scatter Plot")
        x = st.selectbox("X", num_cols, key="xscatter")
        y = st.selectbox("Y", num_cols, key="yscatter")
        color = st.selectbox("Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
        st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)

# =============================================================================
# 💾 4. Export
# =============================================================================

elif section == "💾 Export" and uploaded_file:
    # Récupération du DataFrame nettoyé depuis la session
    df = st.session_state.get("df")
    if df is not None:
        st.subheader("💾 Export du fichier final")
        with st.form("export_form"):
            file_name = st.text_input("Nom du fichier CSV", value="cleaned_data.csv")
            submit = st.form_submit_button("📥 Télécharger")
            if submit:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button("Télécharger le CSV", csv_data, file_name, mime="text/csv")
    else:
        st.warning("❌ Aucune donnée disponible pour l’export.")
