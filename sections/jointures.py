# ============================================================
# Fichier : sections/jointures.py
# Objectif : Fusion intelligente de fichiers avec suggestions
#            et indicateurs de couverture (version Datalyzer)
# Auteur : Xavier Rousseau
# ------------------------------------------------------------
# Notes d'implémentation :
#  - Aligne automatiquement les types de clés (cast str si besoin).
#  - Nettoie le nom d’export/snapshot (safe filename).
#  - Suggestions bornées (colonnes/uniques) pour rester réactif.
#  - UI unifiée : section_header() + show_footer()
#  - Indicateurs fiables via `merge(..., indicator=True)`.
# ============================================================

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import section_header, show_footer


# =============================== Constantes ===================================

# Limites pour calcul des suggestions (contrôle mémoire/temps).
# Idée : on borne le nombre d'unqiues et de colonnes scannées pour éviter
# les OOM et conserver une UI réactive sur des fichiers larges.
SUGGEST_MAX_UNIQUES: int = 50_000        # au-delà, on échantillonne
SUGGEST_SAMPLE_UNIQUES: int = 15_000     # taille d’échantillon de uniques
SUGGEST_MAX_COLS_PER_SIDE: int = 30      # si table avec 200 colonnes…
SUGGEST_MIN_COVERAGE: float = 10.0       # seuil (%) pour afficher une suggestion
PREVIEW_ROWS: int = 10                   # lignes d’aperçu post-jointure


# =============================== Helpers ======================================

def _sanitize_filename(name: str) -> str:
    """
    Produit un nom de fichier « sûr » : alphanumérique + '_' + '-'.

    Paramètres
    ----------
    name : str
        Base proposée par l'utilisateur (peut être vide).

    Retour
    ------
    str
        Nom nettoyé, par défaut "fusion" si tout est vide/invalidé.

    Pourquoi :
    ----------
    Évite les caractères problématiques selon l'OS et les FS (espaces,
    ponctuation exotique, etc.) pour les téléchargements et snapshots.
    """
    name = (name or "").strip()
    name = re.sub(r"[^\w\-]+", "_", name)
    return name.strip("_") or "fusion"


def _stem(fname: str) -> str:
    """
    Renvoie la racine d'un nom de fichier (sans extension).

    Utile pour générer des suffixes de colonnes post-merge.
    Gère des extensions simples (1 à 5 caractères).
    """
    return re.sub(r"\.[A-Za-z0-9]{1,5}$", "", fname)


def _align_key_types(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_on: Sequence[str],
    right_on: Sequence[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[str, str, str]]]:
    """
    Aligne les dtypes des colonnes clés avant la jointure.

    Stratégie :
      - Si divergence de dtype entre `lcol` et `rcol`, cast des DEUX côtés en str.
      - Enregistre un diagnostic lisible pour l'UI (expander).

    Paramètres
    ----------
    df_left, df_right : pd.DataFrame
        DataFrames de gauche et de droite.
    left_on, right_on : list[str]
        Listes alignées de colonnes clés.

    Retour
    ------
    (dl, dr, diagnostics)
        dl, dr sont des copies modifiées et `diagnostics` liste des tuples
        (col_gauche, col_droite, message).
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
    Renvoie les valeurs uniques d'une série, échantillonnées si trop volumineuses.

    Pourquoi :
      - Calculer |∩|, |∪| et les métriques associées peut exploser en mémoire
        si on garde tous les uniques sur de très grosses colonnes (IDs).
      - On échantillonne de façon déterministe (random_state=42).

    Retour
    ------
    pd.Series
        Série des uniques (complète ou échantillonnée).
    """
    uniq = pd.Series(pd.unique(values.dropna()))
    if uniq.size > SUGGEST_MAX_UNIQUES:
        uniq = uniq.sample(n=SUGGEST_SAMPLE_UNIQUES, random_state=42)
    return uniq


def _coverage_metrics(left_vals: pd.Series, right_vals: pd.Series) -> Tuple[float, float, int, int, int]:
    """
    Calcule des métriques de recouvrement entre deux colonnes candidates.

    Définitions
    -----------
    coverage_min (%) = |intersection| / min(|L|, |R|) * 100
      → Mesure la "couverture" minimale si on joignait sur cette paire.

    jaccard (%) = |intersection| / |union| * 100
      → Mesure la similarité globale des ensembles.

    Retour
    ------
    (coverage_min, jaccard, nL, nR, nI)
      coverage_min, jaccard arrondis à 0.1 près.
      nL, nR = tailles des ensembles uniques (après éventuel cap).
      nI = taille de l'intersection.
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
    Propose des paires de colonnes candidates pour la jointure,
    en se basant sur le recouvrement (coverage_min + jaccard).

    Heuristique & Bornes
    --------------------
    - On limite à `SUGGEST_MAX_COLS_PER_SIDE` colonnes par DataFrame.
    - On tolère dtype object des deux côtés (IDs hétérogènes fréquents).
    - On n'affiche que les suggestions au-delà de `SUGGEST_MIN_COVERAGE`.

    Retour
    ------
    pd.DataFrame | None
        Un tableau trié par "Couverture min (%)" desc puis "Jaccard (%)",
        ou None si aucune suggestion pertinente.
    """
    cols_left = df_left.columns.tolist()[:SUGGEST_MAX_COLS_PER_SIDE]
    cols_right = df_right.columns.tolist()[:SUGGEST_MAX_COLS_PER_SIDE]

    suggestions: List[Tuple[str, str, float, float, int, int, int]] = []
    for lcol in cols_left:
        for rcol in cols_right:
            lt, rt = df_left[lcol].dtype, df_right[rcol].dtype
            # On tolère les colonnes object (IDs hétérogènes fréquents).
            if (lt == rt) or pd.api.types.is_object_dtype(lt) or pd.api.types.is_object_dtype(rt):
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
        kind="mergesort",  # stable pour égalités
    ).reset_index(drop=True)


# =============================== Vue principale ================================

def run_jointures() -> None:
    """
    Affiche la page « Jointures intelligentes ».

    Parcours utilisateur :
      1) Sélectionner deux fichiers déjà chargés (gauche/droite).
      2) Consulter les suggestions automatiques (coverage_min + jaccard).
      3) Choisir manuellement les colonnes clés (clés composites possibles).
      4) Lancer la jointure (inner/left/right/outer).
      5) Visualiser les indicateurs de couverture via `_merge`.
      6) Sauvegarder un snapshot + télécharger le CSV résultant.

    Dépendances attendues :
      - `st.session_state["dfs"]` : dict[str, pd.DataFrame] des fichiers chargés.
      - `utils.ui_utils.section_header(...)` : en-tête unifié.
      - `utils.filters.validate_step_button(...)` : validation de l'étape.
      - `utils.snapshot_utils.save_snapshot(df, suffix=...)` : snapshot.
      - `utils.log_utils.log_action(event, details)` : traçabilité.

    Accessibilité :
      - Les blocs d'explication utilisent des titres clairs et des captions.
      - Les tableaux sont rendus via `st.dataframe` (navigation clavier).
    """
    # ---------- En-tête unifié ----------
    section_header(
        title="Jointures intelligentes",
        subtitle="Fusionnez deux fichiers via suggestions ou sélection manuelle des clés.",
        section="jointures",     # → image depuis config.SECTION_BANNERS["jointures"]
        emoji="🔗",
    )

    # ---------- Vérification des fichiers ----------
    dfs = st.session_state.get("dfs", {})
    if not dfs or len(dfs) < 2:
        st.warning("📁 Importez au moins deux fichiers via l’onglet **Chargement**.")
        return

    # Sélection gauche/droite
    fichiers = list(dfs.keys())
    fichier_gauche = st.selectbox("📌 Fichier principal (gauche)", fichiers, key="join_left")
    fichiers_droite = [f for f in fichiers if f != fichier_gauche]
    fichier_droit = st.selectbox("📎 Fichier à joindre (droite)", fichiers_droite, key="join_right")

    df_left = dfs[fichier_gauche]
    df_right = dfs[fichier_droit]

    # ---------- Aperçu rapide des colonnes ----------
    st.markdown("### 🧩 Colonnes disponibles")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{fichier_gauche}**")
        st.code(", ".join(map(str, df_left.columns)))
    with c2:
        st.markdown(f"**{fichier_droit}**")
        st.code(", ".join(map(str, df_right.columns)))

    st.divider()

    # ---------- Suggestions automatiques ----------
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

    # ---------- Sélection manuelle des clés ----------
    st.markdown("### 🛠️ Sélection manuelle des colonnes à joindre")
    left_on = st.multiselect(
        "🔑 Clés du fichier gauche", df_left.columns.tolist(),
        key="left_on", help="Vous pouvez sélectionner plusieurs colonnes (clé composite)."
    )
    right_on = st.multiselect(
        "🔑 Clés du fichier droit", df_right.columns.tolist(),
        key="right_on", help="Le nombre de colonnes doit correspondre à gauche."
    )

    # Affiche des stats rapides pour la sélection courante
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
            help=(
                "Choisissez 'inner' pour ne garder que les correspondances exactes ; "
                "'left' pour conserver toutes les lignes du fichier principal ; "
                "'right' pour conserver toutes les lignes du fichier joint ; "
                "'outer' pour conserver toutes les lignes des deux fichiers."
            ),
        )
        default_name = _sanitize_filename(f"fusion_{_stem(fichier_gauche)}_{_stem(fichier_droit)}")
        nom_fusion = _sanitize_filename(st.text_input("💾 Nom du fichier fusionné", value=default_name))

        # Lancer la jointure
        do_merge = st.button("🔗 Lancer la jointure", type="primary")
        if do_merge:
            try:
                with st.spinner("Fusion en cours…"):
                    # 1) Harmoniser les types de clés (diagnostic affichable)
                    df_left_aligned, df_right_aligned, diag = _align_key_types(
                        df_left, df_right, left_on, right_on
                    )
                    if diag:
                        with st.expander("ℹ️ Alignement de types appliqué", expanded=False):
                            for lcol, rcol, msg in diag:
                                st.write(f"- `{lcol}` ↔ `{rcol}` : {msg}")

                    # 2) Suffixe basé sur le nom du fichier droit (sans extension)
                    right_suffix = f"_{_stem(fichier_droit)}"

                    # 3) Merge avec indicateur de provenance pour métriques fiables
                    fusion = df_left_aligned.merge(
                        df_right_aligned,
                        left_on=list(left_on),
                        right_on=list(right_on),
                        how=type_jointure,
                        suffixes=("", right_suffix),
                        copy=False,
                        sort=False,
                        indicator=True,  # ← nécessaire pour récupérer _merge
                    )

                # 4) Indicateurs de couverture via colonne `_merge`
                vc = fusion["_merge"].value_counts(dropna=False)
                matched = int(vc.get("both", 0))
                only_left = int(vc.get("left_only", 0))
                only_right = int(vc.get("right_only", 0))
                total = int(len(fusion))

                # Nettoyage : retirer `_merge` du rendu final
                fusion = fusion.drop(columns=["_merge"])

                st.success(
                    f"✅ Jointure réussie : {fusion.shape[0]} lignes × {fusion.shape[1]} colonnes "
                    f"(appariées : {matched}, "
                    f"gauche seules : {only_left if type_jointure in {'left','outer'} else 0}, "
                    f"droite seules : {only_right if type_jointure in {'right','outer'} else 0})."
                )

                # 5) Mémoriser + snapshot + log
                st.session_state.setdefault("dfs", {})
                st.session_state["dfs"][f"{nom_fusion}.csv"] = fusion
                st.session_state["df"] = fusion

                save_snapshot(fusion, suffix=nom_fusion)  # cohérent avec la section fichiers
                log_action("jointure", f"{type_jointure} entre {fichier_gauche} et {fichier_droit} → {nom_fusion}")

                # 6) Aperçu & téléchargement
                with st.expander("🔍 Aperçu du résultat", expanded=True):
                    st.dataframe(fusion.head(PREVIEW_ROWS), use_container_width=True)

                st.download_button(
                    label="📥 Télécharger le fichier fusionné (CSV)",
                    data=fusion.to_csv(index=False).encode("utf-8"),
                    file_name=f"{nom_fusion}.csv",
                    mime="text/csv",
                )

            except Exception as e:
                # Message volontairement concis ; le détail peut être logué côté serveur
                st.error(f"❌ Erreur lors de la jointure : {e}")
    else:
        # Guide l'utilisateur vers la condition d'activation :
        # même nombre de colonnes entre gauche et droite.
        st.info("💡 Sélectionnez un nombre **égal** de clés dans les deux fichiers pour activer la jointure.")

    # ---------- Validation d’étape ----------
    # Permet de marquer la progression utilisateur dans le workflow.
    if "df" in st.session_state and isinstance(st.session_state["df"], pd.DataFrame):
        validate_step_button(
            "jointures",
            label="✅ Valider l’étape",
            context_prefix="jointr_",
        )

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
