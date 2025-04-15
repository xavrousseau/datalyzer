# =============================================================================
# 📦 IMPORTATION DES LIBRAIRIES
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import zscore
import csv
from io import StringIO, BytesIO
import psutil
import sys

from eda_utils import (
    detect_variable_types,
    compute_correlation_matrix,
    detect_outliers_iqr,
    detect_constant_columns,
    detect_low_variance_columns,
    encode_categorical,
    plot_missing_values,
    get_columns_above_threshold,
    drop_missing_columns
)
from log_utils import log_transformation

# =============================================================================
# 🎨 CONFIGURATION GLOBALE DE L’APP
# =============================================================================

st.set_page_config(page_title="EDA Explorer – Analyse exploratoire de données", layout="wide")

st.markdown("""
    <style>
        .stButton>button { color: white; background: #0099cc; }
        .stDownloadButton>button { background-color: #28a745; color: white; }
        .stSlider>div { background-color: #f0f0f5; }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 🧭 BARRE DE NAVIGATION
# =============================================================================
section = st.sidebar.radio("🧭 Navigation", [
    "📂 Chargement",
    "🔗 Jointures",
    "🔍 Analyse exploratoire",
    "📊 Analyse catégorielle",
    "🎯 Analyse variable cible",
    "🚨 Qualité des données",
    "🧪 Analyse multivariée",
    "💾 Export",
    "🕰️ Snapshots"   
])

# =============================================================================
# 🔧 UTILITAIRES : Sélection de dataframe actif & Snapshots
# =============================================================================

def select_active_dataframe():
    all_dfs = st.session_state.get("dfs", {})
    if not all_dfs:
        st.warning("❌ Aucun fichier chargé.")
        st.stop()
    selected_name = st.selectbox("📁 Choisissez un fichier à analyser", list(all_dfs.keys()), key="global_df_selector")
    st.session_state["df"] = all_dfs[selected_name]
    return all_dfs[selected_name], selected_name

def save_snapshot(label=None):
    df = st.session_state.get("df")
    if df is None:
        st.warning("Aucune donnée active à sauvegarder.")
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    label = label or "snapshot"
    snapshot_name = f"{label}_{timestamp}"
    if "snapshots" not in st.session_state:
        st.session_state["snapshots"] = {}
    st.session_state["snapshots"][snapshot_name] = df.copy()
    st.success(f"📸 Sauvegarde créée : `{snapshot_name}`")


# =============================================================================
# 📂 Chargement multi-fichiers
# =============================================================================

if section == "📂 Chargement":
    st.title("📊 EDA Explorer – Application d'analyse exploratoire de données")
    st.markdown("---")

    uploaded_files = st.file_uploader("Sélectionnez un ou plusieurs fichiers", type=["csv", "xlsx", "parquet"], accept_multiple_files=True)

    if "dfs" not in st.session_state:
        st.session_state["dfs"] = {}

    if uploaded_files:
        for file in uploaded_files:
            name = file.name
            ext = name.split(".")[-1].lower()
            try:
                if ext == "csv":
                    text = file.read().decode("utf-8", errors="ignore")
                    sep = csv.Sniffer().sniff(text[:2048]).delimiter
                    df = pd.read_csv(StringIO(text), sep=sep)
                elif ext == "xlsx":
                    df = pd.read_excel(file)
                elif ext == "parquet":
                    df = pd.read_parquet(file)
                st.session_state["dfs"][name] = df
                st.success(f"✅ {name} chargé ({df.shape[0]} lignes × {df.shape[1]} colonnes)")
            except Exception as e:
                st.error(f"❌ Erreur avec {name} : {e}")

    if st.session_state["dfs"]:
        main_file = st.selectbox("📌 Choisissez un fichier principal à analyser", list(st.session_state["dfs"].keys()))
        st.session_state["df"] = st.session_state["dfs"][main_file]
        df, selected_name = select_active_dataframe()
        st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")
        st.dataframe(df.head(10))

# =============================================================================
# 🔗 Jointures entre fichiers (avancée avec suggestions + preview)
# =============================================================================

elif section == "🔗 Jointures":
    st.subheader("🔗 Fusion de fichiers via jointure intelligente et personnalisée")

    if "dfs" not in st.session_state or len(st.session_state["dfs"]) < 2:
        st.warning("📁 Il faut importer au moins deux fichiers via la section '📂 Chargement'.")
        st.stop()

    fichiers = list(st.session_state["dfs"].keys())
    fichier_gauche = st.selectbox("📌 Fichier principal (gauche)", fichiers, key="join_left")
    fichiers_droite = [f for f in fichiers if f != fichier_gauche]
    fichier_droit = st.selectbox("📎 Fichier à joindre (droite)", fichiers_droite, key="join_right")

    df_left = st.session_state["dfs"][fichier_gauche]
    df_right = st.session_state["dfs"][fichier_droit]

    st.markdown("### 🧩 Aperçu des colonnes")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{fichier_gauche}**")
        st.code(", ".join(df_left.columns))
    with col2:
        st.markdown(f"**{fichier_droit}**")
        st.code(", ".join(df_right.columns))

    st.markdown("### 🤖 Suggestions automatiques de colonnes à joindre")
    suggestions = []
    for col_left in df_left.columns:
        for col_right in df_right.columns:
            if df_left[col_left].dtype == df_right[col_right].dtype:
                uniques_left = set(df_left[col_left].dropna().unique())
                uniques_right = set(df_right[col_right].dropna().unique())
                if not uniques_left or not uniques_right:
                    continue
                intersection = len(uniques_left & uniques_right) / min(len(uniques_left), len(uniques_right))
                if intersection > 0.5:
                    suggestions.append((col_left, col_right, round(intersection * 100, 1)))

    if suggestions:
        df_suggest = pd.DataFrame(suggestions, columns=["Colonne gauche", "Colonne droite", "Correspondance (%)"])
        st.dataframe(df_suggest.sort_values("Correspondance (%)", ascending=False), use_container_width=True)
    else:
        st.info("Aucune correspondance automatique trouvée. Veuillez sélectionner manuellement.")

    st.markdown("### 🔧 Sélection manuelle des colonnes pour la jointure")
    left_on = st.multiselect("🔑 Colonnes du fichier gauche", df_left.columns.tolist(), key="left_on_manual")
    right_on = st.multiselect("🔑 Colonnes du fichier droit", df_right.columns.tolist(), key="right_on_manual")

    if left_on and right_on and len(left_on) == len(right_on):
        st.markdown("### 🔍 Comparaison des colonnes sélectionnées")

        preview_stats = []
        for l_col, r_col in zip(left_on, right_on):
            uniques_left = set(df_left[l_col].dropna().unique())
            uniques_right = set(df_right[r_col].dropna().unique())
            common = uniques_left & uniques_right
            if uniques_left and uniques_right:
                coverage = len(common) / min(len(uniques_left), len(uniques_right)) * 100
            else:
                coverage = 0
            preview_stats.append({
                "Colonne gauche": l_col,
                "Colonne droite": r_col,
                "Uniques gauche": len(uniques_left),
                "Uniques droite": len(uniques_right),
                "Communes": len(common),
                "Correspondance (%)": round(coverage, 1)
            })

        st.dataframe(pd.DataFrame(preview_stats), use_container_width=True)

        type_jointure = st.radio("⚙️ Type de jointure", ["inner", "left", "right", "outer"], horizontal=True)
        nom_fusion = st.text_input("💾 Nom du nouveau fichier fusionné", value=f"fusion_{fichier_gauche}_{fichier_droit}")

        if st.button("🔗 Lancer la jointure personnalisée"):
            try:
                fusion = df_left.merge(
                    df_right,
                    left_on=left_on,
                    right_on=right_on,
                    how=type_jointure,
                    suffixes=('', f"_{fichier_droit.split('.')[0]}")
                )
                st.session_state["dfs"][nom_fusion] = fusion
                st.session_state["df"] = fusion
                save_snapshot(label=nom_fusion)
                st.success(f"✅ Jointure réussie ! {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes.")
                st.write(f"✅ Fichier accessible sous : `{nom_fusion}`")
                st.dataframe(fusion.head(10), use_container_width=True)

                csv_data = fusion.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Télécharger le fichier fusionné", csv_data, f"{nom_fusion}.csv", mime="text/csv")
            except Exception as e:
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        st.warning("⚠️ Veuillez sélectionner un même nombre de colonnes à gauche et à droite pour effectuer la jointure.")


        
# =============================================================================
# 🔍 Analyse exploratoire
# =============================================================================
if section == "🔍 Analyse exploratoire":
    st.subheader("🔍 Analyse exploratoire")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📌 Types de variables", "📉 Valeurs manquantes", "📈 Histogrammes", "🚨 Outliers",
        "🧹 Nettoyage auto", "🧼 Nettoyage manuel", "📐 Stats descriptives", "🧬 Corrélations avancées"
    ])

    with tab1:
        st.markdown("### 📌 Types de variables détectées")
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

    with tab2:
        seuil_pct = st.slider("🛠️ Seuil (%) de valeurs manquantes", 0, 100, 20)
        seuil = seuil_pct / 100
        top_n = st.slider("📌 Top colonnes à afficher", 5, 50, 15)
        fig = plot_missing_values(df, seuil=seuil, top_n=top_n)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ Aucune valeur manquante.")
        cols_to_remove = get_columns_above_threshold(df, seuil=seuil)
        if cols_to_remove and st.checkbox("❌ Supprimer ces colonnes"):
            df, dropped = drop_missing_columns(df, seuil=seuil)
            st.session_state.df = df
            log_transformation(f"{len(dropped)} colonnes supprimées pour seuil {seuil_pct}%")
            st.success(f"{len(dropped)} colonnes supprimées.")

    with tab3:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            selected_num = st.selectbox("📊 Choisissez une variable", num_cols)
            st.plotly_chart(px.histogram(df, x=selected_num), use_container_width=True)

    with tab4:
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        col = st.selectbox("Variable à analyser", num_cols, key="iqr_col")
        outliers = detect_outliers_iqr(df, col)
        st.write(f"🔍 {len(outliers)} outliers détectés.")
        st.dataframe(outliers)

    with tab5:
        st.write("🔸 Colonnes constantes :", detect_constant_columns(df))
        st.write("🔸 Faible variance :", detect_low_variance_columns(df))
        
    with tab6:
        st.markdown("### 🔁 Détection et gestion des doublons")

        selected_cols = st.multiselect(
            "🔑 Colonnes à utiliser pour identifier les doublons",
            df.columns.tolist(),
            help="Sélectionnez une ou plusieurs colonnes. Si aucune n'est sélectionnée, la détection se fera sur toutes les colonnes."
        )

        if selected_cols:
            dupes = df[df.duplicated(subset=selected_cols, keep=False)]
        else:
            dupes = df[df.duplicated(keep=False)]

        if not dupes.empty:
            st.warning(f"⚠️ {dupes.shape[0]} doublons détectés.")
            if st.checkbox("👁️ Afficher les lignes en doublon", value=True):
                st.dataframe(dupes)

            if st.button("❌ Supprimer les doublons détectés"):
                initial_len = len(df)
                df = df.drop_duplicates(subset=selected_cols if selected_cols else None)
                st.session_state.df = df
                save_snapshot(label="deduplicated")
                log_transformation(f"{initial_len - len(df)} doublons supprimés sur colonnes : {selected_cols or 'toutes'}")
                st.success(f"✅ {initial_len - len(df)} doublons supprimés.")
        else:
            st.success("✅ Aucun doublon détecté avec ces paramètres.")

        st.markdown("---")
        st.markdown("### 🧼 Suppression manuelle de colonnes")

        cols_to_drop = st.multiselect("Colonnes à supprimer", df.columns.tolist())
        if cols_to_drop and st.button("🗑️ Supprimer les colonnes sélectionnées"):
            df.drop(columns=cols_to_drop, inplace=True)
            st.session_state.df = df
            save_snapshot(label="manual_cleanup")
            log_transformation(f"Colonnes supprimées manuellement : {', '.join(cols_to_drop)}")
            st.success("✅ Colonnes supprimées.")


    with tab7:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            stats = df[num_cols].describe().T
            st.dataframe(stats, use_container_width=True)

    with tab8:
        method = st.radio("📐 Méthode de corrélation :", ["pearson", "spearman", "kendall"], horizontal=True)
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques.")
        else:
            corr_matrix = df[numeric_cols].corr(method=method)
            fig = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 📊 Analyse des variables catégorielles
# =============================================================================
elif section == "📊 Analyse catégorielle":
    st.subheader("📊 Analyse des variables catégorielles")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not cat_cols:
        st.warning("⚠️ Aucune variable catégorielle détectée.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Aperçu global", "📊 Barplots", "📈 Fréquences cumulées", "💡 Suggestions d'encodage"
        ])

        with tab1:
            st.markdown("### 📋 Détail des variables catégorielles")
            summary_cat = pd.DataFrame({
                "Colonne": cat_cols,
                "Nb modalités uniques": [df[col].nunique() for col in cat_cols],
                "Modalité la + fréquente": [df[col].mode()[0] if not df[col].mode().empty else "—" for col in cat_cols],
                "Valeurs manquantes (%)": [f"{df[col].isna().mean() * 100:.1f} %" for col in cat_cols]
            })
            st.dataframe(summary_cat, use_container_width=True)

        with tab2:
            selected_col = st.selectbox("📌 Choisissez une variable", cat_cols, key="cat_bar")
            top_n = st.slider("🔢 Top modalités à afficher", 3, 30, 10)
            top_vals = df[selected_col].value_counts().head(top_n).reset_index()
            top_vals.columns = ["Modalité", "Fréquence"]
            st.plotly_chart(px.bar(top_vals, x="Modalité", y="Fréquence", text="Fréquence"), use_container_width=True)

        with tab3:
            selected_col = st.selectbox("📈 Choisir une variable", cat_cols, key="cat_freq")
            freq_df = df[selected_col].value_counts(normalize=True).reset_index()
            freq_df.columns = ["Modalité", "Fréquence"]
            freq_df["Fréquence cumulée"] = freq_df["Fréquence"].cumsum()
            freq_df["% Fréquence"] = (freq_df["Fréquence"] * 100).round(2).astype(str) + " %"
            freq_df["% Cumulée"] = (freq_df["Fréquence cumulée"] * 100).round(2).astype(str) + " %"
            st.dataframe(freq_df[["Modalité", "% Fréquence", "% Cumulée"]], use_container_width=True)

        with tab4:
            seuil_card = st.slider("🔧 Seuil max pour OneHot encoding", 2, 50, 10)
            suggestions = []
            for col in cat_cols:
                nb_modal = df[col].nunique()
                if nb_modal <= seuil_card:
                    enc = "OneHot"
                elif nb_modal == 2:
                    enc = "Binaire"
                elif nb_modal > seuil_card:
                    enc = "Ordinal / Embedding"
                else:
                    enc = "À vérifier"
                suggestions.append((col, nb_modal, enc))
            enc_df = pd.DataFrame(suggestions, columns=["Colonne", "Nb modalités", "Encodage suggéré"])
            st.dataframe(enc_df.sort_values("Nb modalités"), use_container_width=True)

# =============================================================================
# 🎯 Analyse orientée variable cible
# =============================================================================

elif section == "🎯 Analyse variable cible":
    st.subheader("🎯 Analyse orientée variable cible")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée.")
    else:
        target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
        target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Corrélations", "📈 Cible par groupe", "📦 Boxplot", "🧮 Nuage de points"
        ])

        with tab1:
            corr = df[num_cols].corr()[target_1].drop(target_1).sort_values(ascending=False)
            st.dataframe(corr)
            st.plotly_chart(px.bar(corr.reset_index(), x="index", y=target_1), use_container_width=True)

        with tab2:
            group_col = st.selectbox("Variable catégorielle", cat_cols, key="groupcol")
            avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

            if target_2:
                avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
                st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

        with tab3:
            cat_col = st.selectbox("X = variable catégorielle", cat_cols, key="box_cat")
            num_col = st.selectbox("Y = variable numérique", num_cols, key="box_num")
            st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

        with tab4:
            x = st.selectbox("X", num_cols, key="xscatter")
            y = st.selectbox("Y", num_cols, key="yscatter")
            color = st.selectbox("Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
            st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)

# =============================================================================
# 🚨 Qualité des données
# =============================================================================

elif section == "🚨 Qualité des données":
    st.subheader("🚨 Problèmes potentiels de qualité des données")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")
    # -------------------------------------------------------------------------
    st.markdown("### 🔍 Colonnes mal typées")
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object")
        if df[col].str.replace(".", "", regex=False).str.replace(",", "", regex=False).str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning("📌 Ces colonnes semblent contenir des valeurs numériques mais sont typées comme 'object' :")
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
    z_outlier_summary = {}
    for col in df.select_dtypes(include="number").columns:
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
    st.markdown("### 📌 Colonnes constantes")
    const_cols = detect_constant_columns(df)
    if const_cols:
        st.warning(f"⚠️ Colonnes constantes détectées ({len(const_cols)}) :")
        st.code(", ".join(const_cols))
    else:
        st.success("✅ Aucune colonne constante détectée.")
# =============================================================================
# 🧪 Analyse multivariée et interactions
# =============================================================================
elif section == "🧪 Analyse multivariée":
    st.subheader("🧪 Analyse multivariée et interactions")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    tab1, tab2, tab3 = st.tabs([
        "📉 ACP (PCA)",
        "📊 Interactions num ↔ cat",
        "📚 Corrélation catégorielle"
    ])

    # -------------------------------------------------------------------------
    # Onglet 1 – ACP
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📉 Analyse en Composantes Principales (ACP / PCA)")
        st.info("Réduction des dimensions tout en conservant un maximum d'information.")

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour l'ACP.")
        else:
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA

            df_pca = df[num_cols].dropna()
            if df_pca.empty:
                st.error("❌ Pas assez de lignes complètes pour effectuer une ACP. Veuillez nettoyer ou imputer les données.")
            else:
                df_scaled = StandardScaler().fit_transform(df_pca)

                n_comp = st.slider("Nombre de composantes", 2, min(10, len(num_cols)), 2)
                pca = PCA(n_components=n_comp)
                components = pca.fit_transform(df_scaled)

                pca_df = pd.DataFrame(components, columns=[f"PC{i+1}" for i in range(n_comp)], index=df_pca.index)

                color_cat = st.selectbox("Colorer par (optionnel)", [None] + cat_cols)
                if color_cat:
                    pca_df[color_cat] = df.loc[pca_df.index, color_cat]

                st.markdown("#### 🌈 Projection des données (PC1 vs PC2)")
                fig = px.scatter(pca_df, x="PC1", y="PC2", color=color_cat if color_cat else None)
                st.plotly_chart(fig, use_container_width=True)

                explained = pd.DataFrame({
                    "Composante": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
                    "Variance expliquée (%)": (pca.explained_variance_ratio_ * 100).round(2)
                })
                st.markdown("#### 📈 Variance expliquée")
                st.dataframe(explained)

    # -------------------------------------------------------------------------
    # Onglet 2 – Num ↔ Cat interactions
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 📊 Analyse croisée numérique / catégorielle")
        if not cat_cols or not num_cols:
            st.warning("⚠️ Il faut au moins une variable catégorielle et une numérique.")
        else:
            cat_var = st.selectbox("Variable catégorielle", cat_cols, key="group_cat")
            num_var = st.selectbox("Variable numérique", num_cols, key="group_num")
            st.plotly_chart(px.box(df, x=cat_var, y=num_var), use_container_width=True)

    # -------------------------------------------------------------------------
    # Onglet 3 – Corrélation catégorielle (Cramér's V)
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### 📚 Corrélations entre variables catégorielles (Cramér's V)")
        st.info("Mesure la force d'association entre deux variables catégorielles.")

        if len(cat_cols) < 2:
            st.warning("⚠️ Pas assez de colonnes catégorielles.")
        else:
            from scipy.stats import chi2_contingency

            def cramers_v(x, y):
                confusion_matrix = pd.crosstab(x, y)
                chi2 = chi2_contingency(confusion_matrix)[0]
                n = confusion_matrix.sum().sum()
                phi2 = chi2 / n
                r, k = confusion_matrix.shape
                phi2corr = max(0, phi2 - ((k - 1)*(r - 1)) / (n - 1))
                rcorr = r - ((r - 1)**2) / (n - 1)
                kcorr = k - ((k - 1)**2) / (n - 1)
                return np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))

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
# 🕰️ Snapshots – Historique et restauration
# =============================================================================
elif section == "🕰️ Snapshots":
    st.subheader("🕰️ Historique des snapshots de données")

    snapshots = st.session_state.get("snapshots", {})
    if not snapshots:
        st.info("📭 Aucun snapshot enregistré pour le moment.")
    else:
        selected_snapshot = st.selectbox("📜 Sélectionnez un snapshot à explorer :", list(snapshots.keys()))
        df_snapshot = snapshots[selected_snapshot]

        st.markdown(f"### 📋 Aperçu du snapshot : `{selected_snapshot}`")
        st.write(f"📐 Dimensions : {df_snapshot.shape[0]} lignes × {df_snapshot.shape[1]} colonnes")
        st.dataframe(df_snapshot.head(10), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Restaurer ce snapshot comme fichier actif"):
                st.session_state["df"] = df_snapshot.copy()
                st.success(f"✅ Snapshot `{selected_snapshot}` restauré avec succès.")

        with col2:
            if st.button("🗑️ Supprimer ce snapshot"):
                del st.session_state["snapshots"][selected_snapshot]
                st.success(f"🗑️ Snapshot `{selected_snapshot}` supprimé.")
                st.experimental_rerun()


# =============================================================================
# 💾 Export du fichier final
# =============================================================================

elif section == "💾 Export":
    st.subheader("💾 Export du fichier final")
    df, selected_name = select_active_dataframe()
    st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")  

    df = st.session_state.get("df")
    if df is not None:
        with st.form("export_form"):
            file_name = st.text_input("Nom du fichier CSV", value="cleaned_data.csv")
            submit = st.form_submit_button("📥 Télécharger")
            if submit:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Télécharger le CSV", csv_data, file_name, mime="text/csv")
    else:
        st.warning("❌ Aucune donnée disponible pour l’export.")
