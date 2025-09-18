# ============================================================
# Fichier : sections/export.py
# Objectif : Export des données avec sélection de colonnes ET de lignes,
#            format, logs, snapshot et téléchargement
# Version  : enrichie (filtres ET/OU, échantillon, top-N, dédup, NA)
# Auteur   : Xavier Rousseau — commentaires & docs pédagogiques ajoutés
# ============================================================

from __future__ import annotations

import os
import re
import time
from typing import Tuple, Optional, List

import numpy as np
import pandas as pd
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import section_header, show_footer  # ← en-tête/pied unifiés

# =============================================================================
# Helpers — petites fonctions utilitaires, pures et testables
# =============================================================================

def _sanitize_filename(name: str) -> str:
    """Nettoie un nom brut pour produire un nom de fichier « sûr ».

    Règles appliquées :
      - Trim des espaces, remplacement des caractères non alphanumériques par « _ »
      - Conservation uniquement de `[A-Za-z0-9_-.]`
      - Compression des underscores consécutifs, suppression des `_`/`.` en bord
      - Valeur de repli : "export" si tout est vide

    Pourquoi :
      - Éviter les caractères problématiques pour différents OS/navigateurs
      - Garantir un nom stable pour l'écriture disque et le bouton de DL

    Args:
        name: Nom saisi par l'utilisateur (peut être vide ou bruité)

    Returns:
        Nom assaini prêt à être joint à une extension
    """
    name = (name or "").strip()
    name = re.sub(r"[^\w\-.]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_.")
    return name or "export"


def _ensure_extension(filename: str, file_format: str) -> str:
    """Force l'extension cohérente avec le format demandé.

    Exemples :
      - ("report", "csv")   → "report.csv"
      - ("data.JSON", "json") → "data.JSON" (déjà OK, insensible à la casse)

    Args:
        filename: Nom de base (avec ou sans extension)
        file_format: Format cible parmi {csv, xlsx, json, parquet}

    Returns:
        Nom terminé par l'extension correcte
    """
    ext = file_format.lower()
    if not filename.lower().endswith(f".{ext}"):
        return f"{filename}.{ext}"
    return filename


def _mime_for(fmt: str) -> str:
    """Retourne le type MIME attendu par `st.download_button`.

    Remarque : Parquet n'a pas un unique MIME officiel universellement reconnu,
    on utilise un binaire générique.
    """
    return {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "parquet": "application/octet-stream",
    }.get(fmt, "application/octet-stream")


def _dtype_kind(s: pd.Series) -> str:
    """Détecte une « famille » de type de données pour piloter l'UI et les opérateurs.

    Catégories retournées :
      - "numeric"  : colonnes numériques (int/float/decimal)
      - "datetime" : colonnes datetime64 (toutes variantes)
      - "bool"     : booléens
      - "text"     : fallback (objets/strings)

    Args:
        s: Série pandas dont on veut connaître la famille de type

    Returns:
        Nom de la famille de type (voir ci-dessus)
    """
    if pd.api.types.is_bool_dtype(s):
        return "bool"
    if pd.api.types.is_numeric_dtype(s):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "datetime"
    return "text"


def _build_rule_mask(
    df: pd.DataFrame,
    col: str,
    op: str,
    v1: Optional[str],
    v2: Optional[str],
) -> pd.Series:
    """Construit un masque booléen pour une règle de filtrage (sans `.query`).

    La logique s'adapte dynamiquement au type de la colonne et à l'opérateur.
    Les valeurs v1/v2 proviennent des widgets Streamlit (donc strings et potentiels
    NaN/vides) ; elles sont *castées* de manière tolérante.

    Exemple d'usage :
        mask = _build_rule_mask(df, "age", ">=", "30", None)
        df_filt = df[mask]

    Args:
        df: DataFrame source
        col: Nom de la colonne ciblée
        op: Opérateur choisi (ex: '==', 'between', 'contains', ...)
        v1: Première valeur (ou None/"" si non applicable)
        v2: Seconde valeur (pour 'between' notamment)

    Returns:
        pd.Series booléenne indexée comme `df` (True = ligne conservée)
    """
    s = df[col]
    kind = _dtype_kind(s)

    # — Cas universels : tests de nullité —
    if op == "is null":
        return s.isna()
    if op == "is not null":
        return s.notna()

    # — Casting des entrées selon le type détecté —
    if kind == "numeric":
        def _to_num(x):
            try:
                return float(x)
            except Exception:
                return np.nan
        a = _to_num(v1)
        b = _to_num(v2) if v2 is not None else np.nan
    elif kind == "datetime":
        a = pd.to_datetime(v1, errors="coerce") if v1 is not None else pd.NaT
        b = pd.to_datetime(v2, errors="coerce") if v2 is not None else pd.NaT
    elif kind == "bool":
        # On tolère plusieurs écritures (fr/en/numériques)
        map_bool = {"true": True, "false": False, "1": True, "0": False, "vrai": True, "faux": False}
        val = (v1 or "").strip().lower()
        a = map_bool.get(val, None)
    else:  # text
        a = "" if v1 is None else str(v1)
        b = "" if v2 is None else str(v2)

    # — Opérateurs contextualisés par type —
    if kind == "numeric":
        if op == "==": return s == a
        if op == "!=": return s != a
        if op == "<":  return s < a
        if op == "<=": return s <= a
        if op == ">":  return s > a
        if op == ">=": return s >= a
        if op == "between":
            return s.between(a, b, inclusive="both")

    elif kind == "datetime":
        if op == "==": return s == a
        if op == "!=": return s != a
        if op == "before": return s < a
        if op == "after":  return s > a
        if op == "between":
            return s.between(a, b, inclusive="both")

    elif kind == "bool":
        # Valeur booléenne non reconnue → masque False partout (fail-safe)
        if a is None:
            return pd.Series(False, index=s.index)
        if op == "==": return s == a
        if op == "!=": return s != a

    else:  # text
        # Pour le texte, on opère sur une vue string (gère NaN proprement)
        sv = s.astype("string")
        if op == "==": return sv.fillna("") == a
        if op == "!=": return sv.fillna("") != a
        if op == "contains":     return sv.fillna("").str.contains(a, case=False, na=False)
        if op == "not contains": return ~sv.fillna("").str.contains(a, case=False, na=False)
        if op == "startswith":   return sv.fillna("").str.startswith(a, na=False)
        if op == "endswith":     return sv.fillna("").str.endswith(a, na=False)

    # — Opérateur non géré : par sécurité, on exclut tout —
    return pd.Series(False, index=s.index)


def _operators_for(s: pd.Series) -> List[str]:
    """Retourne la liste d'opérateurs pertinents pour une colonne donnée.

    L'UI peut utiliser ce résultat pour limiter les choix de l'utilisateur
    à des combinaisons cohérentes (ex: 'between' pour numériques/dates, etc.).
    """
    kind = _dtype_kind(s)
    if kind == "numeric":
        return ["==", "!=", "<", "<=", ">", ">=", "between", "is null", "is not null"]
    if kind == "datetime":
        return ["==", "!=", "before", "after", "between", "is null", "is not null"]
    if kind == "bool":
        return ["==", "!=", "is null", "is not null"]
    return ["==", "!=", "contains", "not contains", "startswith", "endswith", "is null", "is not null"]


# =============================================================================
# Vue principale — orchestratrice de la page d'export
# =============================================================================

def run_export() -> None:
    """Affiche la page « Export du fichier final » et orchestre l'export.

    La fonction suit un pipeline *lisible* :
      1) Contexte & en-tête
      2) Sélection des colonnes à inclure
      3) Sélection des lignes (tout / règles AND-OR / échantillon / Top-N trié)
      4) Nettoyage optionnel (dropna, déduplication)
      5) Prévisualisation rapide du résultat
      6) Paramétrage du format (CSV/XLSX/JSON/Parquet), encodage et compression
      7) Écriture disque + bouton de téléchargement + log + snapshot

    Design d'UX :
      - Messages clairs (compteurs de lignes/colonnes, avertissements)
      - Valeurs par défaut sûres, widgets guidés par type de données
      - Évitement de `.query` pour garder le typage explicite et la robustesse
    """
    # ---------- 1) En-tête unifié ----------
    section_header(
        title="Export du fichier final",
        subtitle="Choisissez les colonnes, les lignes, le format — puis téléchargez.",
        section="export",
        emoji="",
    )

    # ---------- 2) DF actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    st.markdown(f"🔎 **Fichier actif : `{nom}`** — **{df.shape[0]}** lignes × **{df.shape[1]}** colonnes")

    # ---------- 3) Colonnes à inclure ----------
    st.subheader("🧩 Colonnes à inclure")
    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à exporter",
        options=df.columns.tolist(),
        default=df.columns.tolist(),
        help="Décochez les colonnes inutiles pour un export plus léger."
    )
    st.write(f"🔢 **{len(selected_columns)} colonne(s) sélectionnée(s)**")
    if not selected_columns:
        st.info("Sélectionnez au moins une colonne pour poursuivre.")
        return

    # ---------- 4) Lignes à exporter ----------
    st.subheader("🎚️ Lignes à exporter")
    mode = st.radio(
        "Source des lignes",
        ["Toutes les lignes", "Filtrer avec des règles", "Échantillon aléatoire", "Top N trié"],
        horizontal=True,
    )

    # Par défaut : on emporte tout, puis on spécialise selon le mode
    df_rows = df

    # ---- 4.a) Filtrer avec des règles (AND/OR) ----
    if mode == "Filtrer avec des règles":
        combi = st.radio("Combinaison des règles", ["ET", "OU"], horizontal=True)
        nb_rules = st.number_input("Nombre de règles", min_value=1, max_value=5, value=1, step=1)

        masks: List[pd.Series] = []
        for i in range(int(nb_rules)):
            st.markdown(f"**Règle {i+1}**")

            # 1) Choix de la colonne
            col = st.selectbox(
                f"Colonne #{i+1}",
                options=df.columns.tolist(),
                key=f"rule_col_{i}",
            )

            # 2) Opérateur contextualisé par type
            ops = _operators_for(df[col])
            op = st.selectbox(
                f"Opérateur #{i+1}",
                options=ops,
                key=f"rule_op_{i}",
            )

            # 3) Widgets de saisie adaptés à l'opérateur et au type
            v1 = v2 = None
            kind = _dtype_kind(df[col])
            if op in {"is null", "is not null"}:
                # Aucun paramètre requis
                pass
            elif op == "between":
                if kind == "datetime":
                    # Sélecteurs de dates Streamlit → Timestamp pandas
                    d1 = st.date_input(f"Valeur min #{i+1}")
                    d2 = st.date_input(f"Valeur max #{i+1}")
                    v1 = pd.Timestamp(d1)
                    v2 = pd.Timestamp(d2)
                elif kind == "numeric":
                    c1, c2 = st.columns(2)
                    v1 = c1.text_input(f"Min #{i+1}", value="")
                    v2 = c2.text_input(f"Max #{i+1}", value="")
                else:
                    # Cas texte : interprété comme bornes lexicales
                    v1 = st.text_input(f"Min #{i+1}", value="")
                    v2 = st.text_input(f"Max #{i+1}", value="")
            else:
                # Opérateurs à une seule valeur
                if kind == "datetime":
                    d = st.date_input(f"Valeur #{i+1}")
                    v1 = pd.Timestamp(d)
                elif kind == "bool":
                    v1 = st.selectbox(
                        f"Valeur #{i+1}",
                        options=["true", "false", "1", "0", "vrai", "faux"],
                        index=0,
                    )
                elif kind == "numeric":
                    v1 = st.text_input(f"Valeur #{i+1}", value="")
                else:
                    v1 = st.text_input(f"Valeur #{i+1}", value="")

            # 4) Construction robuste du masque (avec garde-fous)
            try:
                mask = _build_rule_mask(
                    df,
                    col,
                    op,
                    None if v1 == "" else v1,
                    None if v2 == "" else v2,
                )
            except Exception as e:
                st.error(f"Règle {i+1} invalide : {e}")
                mask = pd.Series(False, index=df.index)
            masks.append(mask)

        # 5) Agrégation ET/OU des masques
        if masks:
            if combi == "ET":
                final_mask = masks[0]
                for m in masks[1:]:
                    final_mask = final_mask & m
            else:  # OU
                final_mask = masks[0]
                for m in masks[1:]:
                    final_mask = final_mask | m
            df_rows = df[final_mask]

        st.info(f"🔎 Lignes correspondantes : **{len(df_rows)}** / {len(df)}")

    # ---- 4.b) Échantillon aléatoire ----
    if mode == "Échantillon aléatoire":
        c1, c2 = st.columns(2)
        n = c1.number_input(
            "Taille de l’échantillon (n)",
            min_value=1,
            max_value=max(1, len(df)),
            value=min(1000, len(df)),
        )
        seed = c2.number_input("Graine aléatoire (seed)", min_value=0, max_value=999999, value=42)

        if n > len(df):
            st.warning("La taille demandée dépasse la taille du dataset : on utilisera tout le dataset.")
            n = len(df)
        df_rows = df.sample(n=int(n), random_state=int(seed))

    # ---- 4.c) Top N trié ----
    if mode == "Top N trié":
        sort_col = st.selectbox("Trier par", options=df.columns.tolist())
        ascending = st.toggle("Tri croissant", value=False)
        n = st.number_input("Nombre de lignes (Top N)", min_value=1, max_value=max(1, len(df)), value=min(1000, len(df)))

        # Optionnel : on ignore les NaN pour un tri plus lisible
        dropna_sort = st.checkbox("Ignorer les NaN pour le tri", value=True)
        tmp = df if not dropna_sort else df[df[sort_col].notna()]
        df_rows = tmp.sort_values(by=sort_col, ascending=ascending).head(int(n))

    # ---------- 5) Nettoyage optionnel des lignes sélectionnées ----------
    st.subheader("🧹 Nettoyage optionnel des lignes sélectionnées")
    c1, c2, c3 = st.columns(3)
    dedup_on = c1.checkbox(
        "Supprimer les doublons",
        value=False,
        help="Supprime les lignes dupliquées sur un sous-ensemble de colonnes."
    )
    dropna_rows = c2.checkbox("Supprimer les lignes avec NA (colonnes choisies)", value=False)
    keep_first = c3.radio(
        "Conserver en cas de doublons",
        ["first", "last"],
        horizontal=True,
        index=0,
        disabled=not dedup_on,
    )

    dedup_subset: List[str] = []
    if dedup_on:
        dedup_subset = st.multiselect(
            "Colonnes utilisées pour la déduplication",
            options=selected_columns,
            default=selected_columns,
            help="Définissez la notion de doublon (par défaut : mêmes valeurs sur toutes les colonnes exportées).",
        )

    # Application effective du nettoyage, sur une copie (immutabilité soft)
    df_rows_clean = df_rows.copy()
    if dropna_rows:
        df_rows_clean = df_rows_clean.dropna(subset=selected_columns, how="any")
    if dedup_on:
        df_rows_clean = df_rows_clean.drop_duplicates(subset=dedup_subset or None, keep=keep_first)

    # ---------- 6) Aperçu (post-filtres/tri/échantillon/dédup) ----------
    with st.expander("🔍 Aperçu du résultat (après filtres/tri/échantillon/dédup)", expanded=False):
        st.dataframe(df_rows_clean[selected_columns].head(50), use_container_width=True)
    st.caption(f"Résultat courant : **{len(df_rows_clean)}** lignes × **{len(selected_columns)}** colonnes")

    # ---------- 7) Options de base d'export ----------
    include_index = st.checkbox("Inclure l’index dans le fichier exporté", value=False)

    st.subheader("📦 Format du fichier")
    file_format = st.selectbox("Format", options=["csv", "xlsx", "json", "parquet"], index=0)

    col_enc, col_comp = st.columns(2)
    with col_enc:
        encoding = (
            st.selectbox(
                "Encodage (CSV/JSON)",
                options=["utf-8", "utf-8-sig", "latin-1"],
                index=0,
                help="UTF-8 recommandé. 'utf-8-sig' utile pour Excel ancien ; 'latin-1' seulement si outil incompatible UTF-8.",
            )
            if file_format in {"csv", "json"}
            else "utf-8"
        )
    with col_comp:
        compression = (
            st.selectbox(
                "Compression",
                options=["aucune", "gzip"],
                index=0,
                help="CSV/JSON/Parquet supportent gzip. XLSX est déjà compressé.",
            )
            if file_format in {"csv", "json", "parquet"}
            else "aucune"
        )

    # ---------- 8) Nom de fichier ----------
    ts = int(time.time())
    default_base = _sanitize_filename(f"export_final_{ts}")
    file_name_input = st.text_input(
        "Nom du fichier exporté (sans extension ou avec extension correspondante)",
        value=default_base,
    )
    file_name_input = _sanitize_filename(file_name_input)
    file_name = _ensure_extension(file_name_input, file_format)

    # ---------- 9) Action d'export ----------
    st.subheader("⬇️ Génération du fichier")
    if st.button("📥 Générer et télécharger le fichier", type="primary"):
        try:
            # (1) Sous-ensemble final (lignes + colonnes)
            df_export = df_rows_clean[selected_columns]

            # (2) Répertoire cible persistant
            export_dir = os.path.join("data", "exports")
            os.makedirs(export_dir, exist_ok=True)  # idempotent
            export_path = os.path.join(export_dir, file_name)

            # (3) Écriture selon format
            if file_format == "csv":
                comp = "gzip" if compression == "gzip" else None
                df_export.to_csv(
                    export_path,
                    index=include_index,
                    encoding=encoding,
                    lineterminator="\n",
                    compression=comp,
                )

            elif file_format == "xlsx":
                # XLSX est déjà compressé (ZIP) → pas de gzip par-dessus
                df_export.to_excel(export_path, index=include_index, engine="openpyxl")

            elif file_format == "json":
                comp = "gzip" if compression == "gzip" else None
                df_export.to_json(
                    export_path,
                    orient="records",
                    force_ascii=False,  # respecte l'UTF-8
                    compression=comp,
                )

            elif file_format == "parquet":
                comp = "gzip" if compression == "gzip" else None
                df_export.to_parquet(export_path, index=include_index, compression=comp)

            else:
                # En théorie inaccessible car l'UI borne les choix
                raise ValueError(f"Format non géré : {file_format}")

            # (4) Log + snapshot — utile pour audit et MLOps light
            save_snapshot(df_export, suffix=file_format)
            log_action(
                "export",
                f"{file_name} — rows={len(df_export)} — cols={len(selected_columns)} — "
                f"mode={mode} — format={file_format} — comp={compression}",
            )

            # (5) Bouton de téléchargement (lecture binaire du fichier écrit)
            with open(export_path, "rb") as f:
                payload = f.read()

            st.success(f"✅ Fichier exporté : **{file_name}**")
            st.download_button(
                label="📥 Télécharger maintenant",
                data=payload,
                file_name=file_name,
                mime=_mime_for(file_format),
            )
            st.caption(f"Fichier enregistré sur disque : `{export_path}`")

        except Exception as e:
            # Remontée d'erreur lisible pour l'utilisateur final
            st.error(f"❌ Erreur pendant l’export : {e}")

    # ---------- 10) Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
