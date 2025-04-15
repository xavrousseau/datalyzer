# sections/jointures.py

import streamlit as st
import pandas as pd

from utils.filters import select_active_dataframe
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_transformation


def run_jointures():
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
            coverage = len(common) / min(len(uniques_left), len(uniques_right)) * 100 if uniques_left and uniques_right else 0
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
                log_transformation(f"Jointure {type_jointure} réalisée entre {fichier_gauche} et {fichier_droit}")
                st.success(f"✅ Jointure réussie ! {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes.")
                st.dataframe(fusion.head(10), use_container_width=True)

                csv_data = fusion.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Télécharger le fichier fusionné", csv_data, f"{nom_fusion}.csv", mime="text/csv")
            except Exception as e:
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        st.warning("⚠️ Veuillez sélectionner un même nombre de colonnes à gauche et à droite pour effectuer la jointure.")
