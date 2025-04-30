# ============================================================
# Fichier : jointures.py
# Objectif : Fusion intelligente de fichiers avec suggestions
# et indicateurs de couverture (version finale Streamlit)
# ============================================================

import streamlit as st
import pandas as pd

from utils.filters import select_active_dataframe
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.ui_utils import show_header_image

def run_jointures():
    # 🌅 Image décorative
    show_header_image("bg_temple_sunset.png")

    # 🧭 Titre général
    st.title("🔗 Jointures intelligentes de fichiers")
    st.markdown("_Fusion de snapshots via des clés communes avec suggestions automatiques._")

    st.divider()

    # Vérification
    if "dfs" not in st.session_state or len(st.session_state["dfs"]) < 2:
        st.warning("📁 Il faut importer au moins deux fichiers via 'Chargement'.")
        st.stop()

    # Sélection fichiers
    fichiers = list(st.session_state["dfs"].keys())
    fichier_gauche = st.selectbox("📌 Fichier principal (gauche)", fichiers, key="join_left")
    fichiers_droite = [f for f in fichiers if f != fichier_gauche]
    fichier_droit = st.selectbox("📎 Fichier à joindre (droite)", fichiers_droite, key="join_right")

    df_left = st.session_state["dfs"][fichier_gauche]
    df_right = st.session_state["dfs"][fichier_droit]

    # Aperçu des colonnes
    st.markdown("### 🧩 Colonnes disponibles")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{fichier_gauche}**")
        st.code(", ".join(df_left.columns))
    with col2:
        st.markdown(f"**{fichier_droit}**")
        st.code(", ".join(df_right.columns))

    st.divider()

    # Suggestions automatiques
    st.markdown("### 🤖 Suggestions automatiques de jointure")
    suggestions = []
    for col_left in df_left.columns:
        for col_right in df_right.columns:
            if df_left[col_left].dtype == df_right[col_right].dtype:
                set_left = set(df_left[col_left].dropna().unique())
                set_right = set(df_right[col_right].dropna().unique())
                if not set_left or not set_right:
                    continue
                inter = set_left & set_right
                coverage = len(inter) / min(len(set_left), len(set_right))
                if coverage > 0.5:
                    suggestions.append((col_left, col_right, round(coverage * 100, 1)))

    if suggestions:
        df_suggest = pd.DataFrame(suggestions, columns=["Colonne gauche", "Colonne droite", "Correspondance (%)"])
        st.dataframe(df_suggest.sort_values("Correspondance (%)", ascending=False), use_container_width=True)
    else:
        st.info("Aucune correspondance automatique trouvée.")

    st.divider()

    # Sélection manuelle
    st.markdown("### 🛠️ Sélection manuelle des colonnes à joindre")
    left_on = st.multiselect("🔑 Clés du fichier gauche", df_left.columns.tolist(), key="left_on")
    right_on = st.multiselect("🔑 Clés du fichier droit", df_right.columns.tolist(), key="right_on")

    if left_on and right_on and len(left_on) == len(right_on):
        st.markdown("### 📊 Statistiques de correspondance")
        stats = []
        for l, r in zip(left_on, right_on):
            ul, ur = set(df_left[l].dropna()), set(df_right[r].dropna())
            commun = ul & ur
            couverture = len(commun) / min(len(ul), len(ur)) * 100 if ul and ur else 0
            stats.append({
                "Colonne gauche": l,
                "Colonne droite": r,
                "Uniques gauche": len(ul),
                "Uniques droite": len(ur),
                "Communes": len(commun),
                "Correspondance (%)": round(couverture, 1)
            })
        st.dataframe(pd.DataFrame(stats))

        type_jointure = st.radio("⚙️ Type de jointure", ["inner", "left", "right", "outer"], horizontal=True)
        nom_fusion = st.text_input("💾 Nom du fichier fusionné", value=f"fusion_{fichier_gauche}_{fichier_droit}")

        if st.button("🔗 Lancer la jointure"):
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

                save_snapshot(fusion, label=nom_fusion)
                log_transformation(f"Jointure {type_jointure} entre {fichier_gauche} et {fichier_droit}")

                st.success(f"✅ Jointure réussie : {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes")
                st.dataframe(fusion.head(10), use_container_width=True)

                csv_data = fusion.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Télécharger le fichier fusionné", csv_data, f"{nom_fusion}.csv", mime="text/csv")

            except Exception as e:
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        st.warning("⚠️ Sélectionnez le même nombre de clés dans chaque fichier.")
