# ============================================================
# Fichier : sections/jointures.py
# Objectif : Fusion intelligente de fichiers avec suggestions
#            et indicateurs de couverture (version Datalyzer)
# Notes :
#  - Aucune modification de utils/filters.py nécessaire.
#  - Aligne automatiquement les types de clés (cast str si besoin).
#  - Nettoie le nom d’export/snapshot pour éviter les caractères gênants.
#  - Evite les OOM : suggestions via uniques échantillonnés (bornes).
# ============================================================

from __future__ import annotations

import base64
import re
from io import BytesIO
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st
from PIL import Image

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_icon_header


# =============================== Constantes ===================================

# Limites pour calcul des suggestions (contrôle mémoire/temps)
# - on borne le nombre d'unqiues par colonne (par ex. grosses ID)
# - on borne le nombre de colonnes testées pour éviter O(n^2) trop lourd
SUGGEST_MAX_UNIQUES = 50_000         # au-delà, on échantillonne
SUGGEST_SAMPLE_UNIQUES = 15_000      # taille d'échantillon de uniques
SUGGEST_MAX_COLS_PER_SIDE = 30       # si table avec 200 colonnes…
SUGGEST_MIN_COVERAGE = 10.0          # seuil de "couverture minimale" (%) pour afficher

# Aperçu jointure : n lignes pour l’aperçu visuel
PREVIEW_ROWS = 10


# =============================== Header visuel =================================

def _render_header_image() -> None:
    """
    Affiche une bannière en-tête centrée, avec fallback informatif en cas d'absence.
    Conserve l'approche base64 (style custom) pour éviter les chemins statiques relatifs
    cassés en prod (CDN) — alternative simple : st.image(..., use_container_width=True).
    """
    image_path = "static/images/headers/header_waves_blossoms.png"  # ⚠️ vérifie l’orthographe du fichier
    try:
        img = Image.open(image_path).resize((900, 220))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

        st.markdown(
            f"""
            <div style='display:flex;justify-content:center;margin-bottom:1.5rem;'>
              <img src="data:image/png;base64,{base64_img}" alt="Bannière Datalyzer"
                   style="border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.2);" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        # On informe sans bloquer l'app (image décorative)
        st.info("Aucune image d’en-tête trouvée.")
        st.caption(f"(Détail : {e})")


# =============================== Helpers ======================================

def _sanitize_filename(name: str) -> str:
    """Nom de fichier sûr (alphanumérique + _ -)."""
    name = (name or "").strip()
    name = re.sub(r"[^\w\-]+", "_", name)
    return name.strip("_") or "fusion"


def _stem(fname: str) -> str:
    """Racine de nom de fichier sans extension (utile pour suffixes)."""
    return re.sub(r"\.[A-Za-z0-9]{1,5}$", "", fname)


def _align_key_types(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_on: Sequence[str],
    right_on: Sequence[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[str, str, str]]]:
    """
    Aligne les dtypes des clés de jointure. Stratégie simple et sûre :
    - si divergence, cast en string des deux côtés.
    Retourne (df_left_aligned, df_right_aligned, diagnostics).
    """
    dl, dr = df_left.copy(), df_right.copy()
    diagnostics: List[Tuple[str, str, str]] = []
    for lcol, rcol in zip(left_on, right_on):
        lt, rt = dl[lcol].dtype, dr[rcol].dtype
        if lt != rt:
            diagnostics.append((lcol, rcol, f"{lt} ≠ {rt} → cast en str"))
            dl[lcol] = dl[lcol].astype(str)
            dr[rcol] = dr[rcol].astype(str)
    return dl, dr, diagnostics


def _cap_uniques(values: pd.Series) -> pd.Series:
    """
    Retourne une série des valeurs uniques, échantillonnée si trop volumineuse.
    Conserve la nature 'object' / 'string' / 'int'… mais on travaille par comparaison d'égalité.
    """
    uniq = pd.Series(pd.unique(values.dropna()))
    if uniq.size > SUGGEST_MAX_UNIQUES:
        uniq = uniq.sample(n=SUGGEST_SAMPLE_UNIQUES, random_state=42)
    return uniq


def _coverage_metrics(left_vals: pd.Series, right_vals: pd.Series) -> Tuple[float, float, int, int, int]:
    """
    Calcule des métriques de recouvrement entre deux ensembles de valeurs uniques.
    - coverage_min (%): |∩| / min(|L|, |R|) * 100
    - jaccard (%):      |∩| / |∪| * 100
    Retourne (coverage_min, jaccard, nL, nR, nI)
    """
    set_l = set(_cap_uniques(left_vals).tolist())
    set_r = set(_cap_uniques(right_vals).tolist())
    if not set_l or not set_r:
        return 0.0, 0.0, len(set_l), len(set_r), 0
    inter = set_l & set_r
    union = set_l | set_r
    coverage_min = (len(inter) / max(1, min(len(set_l), len(set_r)))) * 100
    jaccard = (len(inter) / max(1, len(union))) * 100
    return round(coverage_min, 1), round(jaccard, 1), len(set_l), len(set_r), len(inter)


def _suggest_matches(df_left: pd.DataFrame, df_right: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Cherche des paires de colonnes candidates à la jointure par recouvrement d’éléments.
    Renvoie un DataFrame trié (coverage_min desc, puis jaccard), ou None si rien.
    Bornes : on limite le nombre de colonnes explorées pour la réactivité.
    """
    # Colonnes candidates : on prend d'abord les colonnes non trop exotiques
    cols_left = df_left.columns.tolist()[:SUGGEST_MAX_COLS_PER_SIDE]
    cols_right = df_right.columns.tolist()[:SUGGEST_MAX_COLS_PER_SIDE]

    suggestions: List[Tuple[str, str, float, float, int, int, int]] = []
    for lcol in cols_left:
        for rcol in cols_right:
            # Heuristique : on ne compare que si types proches ou si strings (souvent des IDs)
            lt, rt = df_left[lcol].dtype, df_right[rcol].dtype
            if (lt == rt) or (lt == "object") or (rt == "object"):
                cov, jac, nL, nR, nI = _coverage_metrics(df_left[lcol], df_right[rcol])
                if cov >= SUGGEST_MIN_COVERAGE:
                    suggestions.append((lcol, rcol, cov, jac, nL, nR, nI))

    if not suggestions:
        return None

    df_suggest = pd.DataFrame(
        suggestions,
        columns=[
            "Colonne gauche", "Colonne droite",
            "Couverture min (%)", "Jaccard (%)",
            "Uniques gauche", "Uniques droite", "Communes"
        ],
    )
    return df_suggest.sort_values(
        by=["Couverture min (%)", "Jaccard (%)"],
        ascending=False,
        kind="mergesort",  # stable
    ).reset_index(drop=True)


def _post_merge_coverage(
    merged: pd.DataFrame, left_on: Sequence[str], right_on: Sequence[str], how: str
) -> Dict[str, int]:
    """
    Calcule des indicateurs simples de couverture après jointure.
    - lignes appariées vs non appariées selon 'how'
    Utilise des indicateurs d’existance de clés côté gauche/droite.
    """
    # On construit des flags "match_gauche/droite" via présence de toutes les clés
    left_key_present = merged[left_on].notna().all(axis=1)
    right_key_present = merged[right_on].notna().all(axis=1)

    matched = int((left_key_present & right_key_present).sum())
    only_left = int((left_key_present & ~right_key_present).sum())
    only_right = int((~left_key_present & right_key_present).sum())  # valable pour 'right'/'outer'
    total = int(merged.shape[0])

    return {
        "total": total,
        "appariees": matched,
        "gauche_seules": only_left if how in {"left", "outer"} else 0,
        "droite_seules": only_right if how in {"right", "outer"} else 0,
    }


# =============================== Vue principale ================================

def run_jointures() -> None:
    """
    Page "Jointures intelligentes" :
      - Sélection de 2 fichiers chargés (gauche/droite)
      - Suggestions de paires de colonnes (coverage_min + jaccard)
      - Sélection manuelle de clés (multi-colonnes)
      - Jointure (inner/left/right/outer) + indicateurs de couverture
      - Snapshot et téléchargement CSV
    """
    # --- En-tête visuel ---
    _render_header_image()
    show_icon_header(
        "🔗", "Jointures intelligentes",
        "Fusionnez deux fichiers via suggestions ou sélection manuelle des clés."
    )

    # --- Vérification des fichiers préalablement chargés ---
    dfs = st.session_state.get("dfs", {})
    if not dfs or len(dfs) < 2:
        st.warning("📁 Importez au moins deux fichiers via l’onglet **Chargement**.")
        return

    fichiers = list(dfs.keys())
    fichier_gauche = st.selectbox("📌 Fichier principal (gauche)", fichiers, key="join_left")
    fichiers_droite = [f for f in fichiers if f != fichier_gauche]
    fichier_droit = st.selectbox("📎 Fichier à joindre (droite)", fichiers_droite, key="join_right")

    df_left = dfs[fichier_gauche]
    df_right = dfs[fichier_droit]

    # --- Aperçu des colonnes disponibles ---
    st.markdown("### 🧩 Colonnes disponibles")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{fichier_gauche}**")
        st.code(", ".join(map(str, df_left.columns)))
    with c2:
        st.markdown(f"**{fichier_droit}**")
        st.code(", ".join(map(str, df_right.columns)))

    st.divider()

    # --- Suggestions automatiques (bornées et triées) ---
    st.markdown("### 🤖 Suggestions automatiques de jointure")
    df_suggest = _suggest_matches(df_left, df_right)
    if df_suggest is not None:
        st.dataframe(df_suggest, use_container_width=True, height=240)
        st.caption(
            "Couverture minimale = |intersection| / min(|uniques gauche|, |uniques droite|). "
            "Jaccard = |intersection| / |union|."
        )
    else:
        st.info("Aucune correspondance automatique jugée pertinente (≥ 10%).")

    st.divider()

    # --- Sélection manuelle des clés ---
    st.markdown("### 🛠️ Sélection manuelle des colonnes à joindre")
    left_on = st.multiselect(
        "🔑 Clés du fichier gauche", df_left.columns.tolist(),
        key="left_on", help="Vous pouvez sélectionner plusieurs colonnes (clé composite)."
    )
    right_on = st.multiselect(
        "🔑 Clés du fichier droit", df_right.columns.tolist(),
        key="right_on", help="Le nombre de colonnes doit correspondre à gauche."
    )

    # Affiche des stats rapides de recouvrement pour les paires choisies
    if left_on and right_on and len(left_on) == len(right_on):
        st.markdown("### 📊 Statistiques de correspondance (sélection)")
        rows = []
        for l, r in zip(left_on, right_on):
            cov, jac, nL, nR, nI = _coverage_metrics(df_left[l], df_right[r])
            rows.append({
                "Colonne gauche": l,
                "Colonne droite": r,
                "Uniques gauche": nL,
                "Uniques droite": nR,
                "Communes": nI,
                "Couverture min (%)": cov,
                "Jaccard (%)": jac,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # Paramètres de fusion
        type_jointure = st.radio(
            "⚙️ Type de jointure", ["inner", "left", "right", "outer"],
            horizontal=True, index=1,  # left par défaut
            help="Choisissez 'inner' pour ne garder que les correspondances exactes, "
                 "'left' pour conserver toutes les lignes du fichier principal, etc."
        )
        default_name = _sanitize_filename(f"fusion_{_stem(fichier_gauche)}_{_stem(fichier_droit)}")
        nom_fusion = _sanitize_filename(st.text_input("💾 Nom du fichier fusionné", value=default_name))

        # Lancer la jointure
        do_merge = st.button("🔗 Lancer la jointure", type="primary")
        if do_merge:
            try:
                with st.spinner("Fusion en cours…"):
                    # Harmoniser les types de clés
                    df_left_aligned, df_right_aligned, diag = _align_key_types(df_left, df_right, left_on, right_on)
                    if diag:
                        with st.expander("ℹ️ Alignement de types appliqué", expanded=False):
                            for lcol, rcol, msg in diag:
                                st.write(f"- `{lcol}` ↔ `{rcol}` : {msg}")

                    # Suffixe auto basé sur le nom du fichier droit (sans extension)
                    right_suffix = f"_{_stem(fichier_droit)}"

                    fusion = df_left_aligned.merge(
                        df_right_aligned,
                        left_on=list(left_on),
                        right_on=list(right_on),
                        how=type_jointure,
                        suffixes=("", right_suffix),
                        copy=False,
                        sort=False,
                    )

                # Indicateurs de couverture post-jointure
                cov_stats = _post_merge_coverage(fusion, left_on, right_on, type_jointure)
                st.success(
                    f"✅ Jointure réussie : {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes "
                    f"(appariées : {cov_stats['appariees']}, "
                    f"gauche seules : {cov_stats['gauche_seules']}, "
                    f"droite seules : {cov_stats['droite_seules']})."
                )

                # Mémoriser + snapshot
                st.session_state.setdefault("dfs", {})
                st.session_state["dfs"][f"{nom_fusion}.csv"] = fusion
                st.session_state["df"] = fusion

                save_snapshot(fusion, label=nom_fusion)
                log_action("jointure", f"{type_jointure} entre {fichier_gauche} et {fichier_droit} → {nom_fusion}")

                # Aperçu & téléchargement
                with st.expander("🔍 Aperçu du résultat", expanded=True):
                    st.dataframe(fusion.head(PREVIEW_ROWS), use_container_width=True)

                st.download_button(
                    label="📥 Télécharger le fichier fusionné (CSV)",
                    data=fusion.to_csv(index=False).encode("utf-8"),
                    file_name=f"{nom_fusion}.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        st.info("💡 Sélectionnez un nombre **égal** de clés dans les deux fichiers pour activer la jointure.")

    # --- Validation d’étape (signature inchangée de filters.validate_step_button) ---
    if "df" in st.session_state and isinstance(st.session_state["df"], pd.DataFrame):
        validate_step_button(
            "jointures",
            label="✅ Valider l’étape",
            context_prefix="jointr_",
        )
