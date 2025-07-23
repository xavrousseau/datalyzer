# ============================================================
# Fichier : jointures.py
# Objectif : Fusion intelligente de fichiers avec suggestions
# et indicateurs de couverture (version harmonisée Datalyzer)
# ============================================================

import streamlit as st
import pandas as pd

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image, show_icon_header

def run_jointures():
    # === En-tête visuel ===
    show_header_image("bg_temple_sunset.png")
    show_icon_header("🔗", "Jointures intelligentes",
                     "Fusion de fichiers via suggestions ou correspondances manuelles")

    # === Vérification que plusieurs fichiers sont chargés ===
    dfs = st.session_state.get("dfs", {})
    if not dfs or len(dfs) < 2:
        st.warning("📁 Veuillez importer au moins deux fichiers via l’onglet 'Chargement'.")
        return

    fichiers = list(dfs.keys())
    fichier_gauche = st.selectbox("📌 Fichier principal (gauche)", fichiers, key="join_left")
    fichiers_droite = [f for f in fichiers if f != fichier_gauche]
    fichier_droit = st.selectbox("📎 Fichier à joindre (droite)", fichiers_droite, key="join_right")

    df_left = dfs[fichier_gauche]
    df_right = dfs[fichier_droit]

    # === Aperçu des colonnes ===
    st.markdown("### 🧩 Colonnes disponibles")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{fichier_gauche}**")
        st.code(", ".join(df_left.columns))
    with col2:
        st.markdown(f"**{fichier_droit}**")
        st.code(", ".join(df_right.columns))

    st.divider()

    # === Suggestions automatiques de jointure ===
    st.markdown("### 🤖 Suggestions automatiques de jointure")
    suggestions = []
    for col_left in df_left.columns:
        for col_right in df_right.columns:
            if df_left[col_left].dtype == df_right[col_right].dtype:
                inter = set(df_left[col_left].dropna()) & set(df_right[col_right].dropna())
                if len(inter) / max(len(df_left), len(df_right)) > 0.5:
                    suggestions.append((col_left, col_right, round(len(inter) * 100 / max(1, min(len(df_left), len(df_right))), 1)))

    if suggestions:
        df_suggest = pd.DataFrame(suggestions, columns=["Colonne gauche", "Colonne droite", "Correspondance (%)"])
        st.dataframe(df_suggest.sort_values("Correspondance (%)", ascending=False), use_container_width=True)
    else:
        st.info("Aucune correspondance automatique trouvée.")

    st.divider()

    # === Sélection manuelle des colonnes à joindre ===
    st.markdown("### 🛠️ Sélection manuelle des colonnes à joindre")
    left_on = st.multiselect("🔑 Clés du fichier gauche", df_left.columns.tolist(), key="left_on")
    right_on = st.multiselect("🔑 Clés du fichier droit", df_right.columns.tolist(), key="right_on")

    if left_on and right_on and len(left_on) == len(right_on):
        st.markdown("### 📊 Statistiques de correspondance")
        stats = []
        for l, r in zip(left_on, right_on):
            set_l, set_r = set(df_left[l].dropna()), set(df_right[r].dropna())
            commun = set_l & set_r
            couverture = len(commun) / min(len(set_l), len(set_r)) * 100 if set_l and set_r else 0
            stats.append({
                "Colonne gauche": l,
                "Colonne droite": r,
                "Uniques gauche": len(set_l),
                "Uniques droite": len(set_r),
                "Communes": len(commun),
                "Correspondance (%)": round(couverture, 1)
            })
        st.dataframe(pd.DataFrame(stats))

        # === Paramètres de la fusion ===
        type_jointure = st.radio("⚙️ Type de jointure", ["inner", "left", "right", "outer"], horizontal=True)
        nom_fusion = st.text_input("💾 Nom du fichier fusionné", value=f"fusion_{fichier_gauche}_{fichier_droit}")

        # === Fusion & export ===
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
                log_action("jointure", f"{type_jointure} entre {fichier_gauche} et {fichier_droit} → {nom_fusion}")

                st.success(f"✅ Jointure réussie : {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes")
                st.dataframe(fusion.head(10), use_container_width=True)

                st.download_button(
                    label="📥 Télécharger le fichier fusionné",
                    data=fusion.to_csv(index=False).encode("utf-8"),
                    file_name=f"{nom_fusion}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        st.info("💡 Sélectionnez un nombre égal de clés dans les deux fichiers pour activer la jointure.")

    # ✅ Validation si fusion réalisée
    if "df" in st.session_state and isinstance(st.session_state["df"], pd.DataFrame):
        validate_step_button(st.session_state["df"], step_name="jointures")
