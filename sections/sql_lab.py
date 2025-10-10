# ============================================================
# Fichier : sections/sql_lab.py
# Objectif : SQL Lab — Requêtes ad hoc simples (DuckDB)
# Version  : v2-lite (FR, sans alias 'data', UI épurée) + Refresh
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import io
from typing import Dict, Any, List

import pandas as pd
import streamlit as st
from streamlit_ace import st_ace

from utils.ui_utils import section_header, show_footer
from utils.log_utils import log_action
from utils.snapshot_utils import save_snapshot
from utils.sql_bridge import refresh_sql_mirror_from_files  # ⇐ bouton "Actualiser"
from utils.sql_lab import (
    get_duckdb_connection,
    register_all,
    run_query,
    describe_table,
)

# Clés de session utilisées
KEY_DFS = "dfs"            # dict[str, pd.DataFrame] — fichiers/snapshots importés/activés (global app)
SQL_DATASETS = "datasets"  # dict[str, pd.DataFrame] — miroir SQL Lab (alimenté par Chargement/Bridge)


# ------------------------------ Helpers --------------------------------

def _ensure_state() -> None:
    """Initialise les clés de session locales au SQL Lab."""
    st.session_state.setdefault(SQL_DATASETS, {})
    st.session_state.setdefault("last_sql_df", None)
    st.session_state.setdefault("sql_editor_text", "")
    st.session_state.setdefault("sql_selected_table", "")  # mémorise la table choisie (pour reset éditeur)


def _resume_qualite_simple(df: pd.DataFrame) -> pd.DataFrame:
    """
    Résumé minimal par colonne :
      - type
      - % NA
      - 2–3 exemples de modalités (échantillon léger)
    Note perf : on échantillonne sur 1000 lignes max pour rester instantané.
    """
    rows: List[Dict[str, Any]] = []
    sample = df.head(1000)  # bornage pour éviter le coût sur gros jeux
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        na_pct = round(float(s.isna().mean()) * 100.0, 2) if len(s) else 0.0

        # 2–3 exemples "au hasard" (sans faire de value_counts coûteux)
        try:
            uniques = pd.unique(sample[col].dropna())
            if len(uniques) > 3:
                # échantillon pseudo-aléatoire stable
                mod = sample[col].dropna().astype(str).sample(n=3, random_state=42).tolist()
            else:
                mod = [str(x) for x in uniques[:3]]
            mod_txt = ", ".join(mod) if mod else "—"
        except Exception:
            mod_txt = "—"

        rows.append({"colonne": col, "type": dtype, "% NA": na_pct, "exemples": mod_txt})

    return pd.DataFrame(rows)


# -------------------------------- UI -----------------------------------

def render() -> None:
    """
    SQL Lab, version simple :
      - Sélection d'une table (parmi les datasets exposés)
      - Schéma + Résumé qualité minimal (type, %NA, exemples)
      - Éditeur SQL + Exécuter
      - Résultats + Export CSV/Parquet + Snapshot
      - Bouton "Actualiser les tables" pour refléter les modifs d'autres sections
    """
    _ensure_state()

    section_header(
        title="SQL Lab",
        subtitle="Requêtes ponctuelles simples pour vérifier/croiser des données.",
        section="exploration",
        emoji="",
    )

    # Contexte datasets
    dfs_all: Dict[str, pd.DataFrame] = st.session_state.get(KEY_DFS, {})
    datasets: Dict[str, pd.DataFrame] = st.session_state.get(SQL_DATASETS, {})

    # Bouton de rafraîchissement (reconstruit le miroir à partir de dfs)
    # Utile quand une autre section a modifié/créé un DataFrame.
    if st.button("🔄 Actualiser les tables", help="Reconstruit la liste depuis les fichiers chargés/traités."):
        refresh_sql_mirror_from_files()
        datasets = st.session_state.get(SQL_DATASETS, {})  # relit le miroir

    if not dfs_all or not datasets:
        st.warning("❌ Aucune table disponible. Importez/activez un fichier dans **Chargement**.")
        show_footer(author="Xavier Rousseau", site_url="https://xavrousseau.github.io/", version="2.2-lite")
        return

    # Connexion DuckDB et enregistrement DES SEULES tables du miroir
    con = get_duckdb_connection(st.session_state)
    register_all(con, datasets)

    # Liste des tables = exactement les clés du miroir (pas d'alias 'data' ici)
    table_names = list(datasets.keys())

    # Sélecteur de table SQL
    table_sel = st.selectbox(
        "🗂️ Table à analyser",
        options=table_names,
        index=table_names.index(st.session_state["sql_selected_table"]) if st.session_state["sql_selected_table"] in table_names else 0,
        help="Tables issues de vos imports/snapshots et traitements."
    )

    # Si la table sélectionnée change, on réinitialise l'éditeur avec un SELECT lisible
    if table_sel != st.session_state["sql_selected_table"]:
        st.session_state["sql_selected_table"] = table_sel
        st.session_state["sql_editor_text"] = f'SELECT * FROM "{table_sel}" LIMIT 50;'
        st.session_state["last_sql_df"] = None  # on efface l'ancien résultat pour éviter la confusion

    # Mise en page : schéma + résumé (gauche) / éditeur + résultats (droite)
    left, right = st.columns([1, 2], gap="large")

    # ----------------------------- Colonne gauche ------------------------------
    with left:
        st.subheader("Schéma")
        try:
            schema_df = describe_table(con, table_sel)
            st.dataframe(schema_df, use_container_width=True, height=220)
        except Exception as e:
            st.error(f"Erreur schéma : {e}")

        st.subheader("Résumé qualité (simple)")
        df_current = datasets.get(table_sel)
        if isinstance(df_current, pd.DataFrame) and not df_current.empty:
            try:
                # Petit rappel global en tête (lignes × colonnes)
                st.caption(f"Dimensions : {df_current.shape[0]} lignes × {df_current.shape[1]} colonnes")
                rq = _resume_qualite_simple(df_current)
                st.dataframe(rq, use_container_width=True, height=320)
            except Exception:
                st.info("Résumé qualité indisponible pour cette table.")
        else:
            st.caption("Résumé qualité non disponible (table vide ou non-Pandas).")

    # ----------------------------- Colonne droite ------------------------------
    with right:
        st.subheader("Éditeur SQL")

        # Valeur par défaut lisible (mise à jour quand table change — cf. plus haut)
        if not st.session_state["sql_editor_text"]:
            st.session_state["sql_editor_text"] = f'SELECT * FROM "{table_sel}" LIMIT 50;'

        query = st_ace(
            value=st.session_state["sql_editor_text"],
            language="sql",
            theme="monokai",
            height=200,
            auto_update=True,
            show_gutter=True,
            placeholder="Écrivez votre requête SQL ici…",
            key="ace_sql_lab",
        )

        c_run, c_clear = st.columns(2)
        run_btn = c_run.button("▶️ Exécuter", use_container_width=True)
        clear_btn = c_clear.button("🧹 Effacer le résultat", use_container_width=True)

        if clear_btn:
            st.session_state["last_sql_df"] = None
            st.toast("Résultats nettoyés.", icon="🧹")

        # Exécution
        if run_btn:
            sql = (query or f'SELECT * FROM "{table_sel}" LIMIT 50;').strip()
            try:
                df_out = run_query(con, sql)
                st.session_state["last_sql_df"] = df_out
                st.session_state["sql_editor_text"] = query  # persiste le texte de l'éditeur
                log_action("sql_run", sql[:4000])            # journalisation légère
            except Exception as e:
                st.error(f"Erreur SQL : {e}")

        # Résultats + exports
        df_out = st.session_state.get("last_sql_df")
        if isinstance(df_out, pd.DataFrame):
            st.markdown("**Résultats**")
            st.dataframe(df_out, use_container_width=True, height=420)

            c1, c2, c3 = st.columns([1, 1, 2])
            # CSV
            csv = df_out.to_csv(index=False).encode("utf-8")
            c1.download_button(
                "⬇️ Export CSV",
                data=csv,
                file_name="sql_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
            # Parquet
            buf = io.BytesIO()
            df_out.to_parquet(buf, index=False)
            c2.download_button(
                "⬇️ Export Parquet",
                data=buf.getvalue(),
                file_name="sql_results.parquet",
                mime="application/octet-stream",
                use_container_width=True,
            )
            # Snapshot
            snap_name = c3.text_input("Nom du snapshot", value="sql_result")
            if c3.button("💾 Créer le snapshot", use_container_width=True):
                try:
                    save_snapshot(df_out, suffix=snap_name or "sql_result")
                    log_action("sql_snapshot", snap_name[:200])
                    st.success("✅ Snapshot enregistré.")
                except Exception as e:
                    st.error(f"Erreur snapshot : {e}")

    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="2.2-lite",
    )
