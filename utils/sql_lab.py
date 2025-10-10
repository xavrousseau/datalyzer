# ============================================================
# Fichier : utils/sql_lab.py
# Objectif : Utilitaires SQL Lab — connexion DuckDB en mémoire,
#            enregistrement des tables, exécution sécurisée, introspection
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

from typing import Dict, Any, List

import duckdb
import pandas as pd
import pyarrow as pa

try:
    import polars as pl  # polars est optionnel
except Exception:
    pl = None


# --------------------------- Connexion ---------------------------

def get_duckdb_connection(state) -> duckdb.DuckDBPyConnection:
    """
    Retourne une connexion DuckDB réutilisable stockée en session.
    Crée la connexion en mémoire si elle n'existe pas encore.
    """
    if "duckdb" not in state or state.get("duckdb") is None:
        con = duckdb.connect(database=":memory:")
        # Threads raisonnables ; adapte si besoin (0 = auto)
        con.execute("PRAGMA threads=4")
        state["duckdb"] = con
    return state["duckdb"]


# ----------------------- Enregistrement DF -----------------------

def _register_one(con: duckdb.DuckDBPyConnection, name: str, df: Any) -> None:
    """
    Enregistre un DataFrame sous forme de vue DuckDB.
    - Supporte pandas, polars, pyarrow.Table
    - Fallback via pandas.DataFrame
    IMPORTANT : on n'altère PAS le nom ; on suppose que la couche appelante
    (SQL Lab) QUOTE correctement les identifiants dans les requêtes.
    """
    if pl is not None and isinstance(df, pl.DataFrame):
        con.register(name, df.to_arrow())
        return
    if isinstance(df, pd.DataFrame):
        con.register(name, df)
        return
    if isinstance(df, pa.Table):
        con.register(name, df)
        return
    # dernier recours : conversion en pandas
    con.register(name, pd.DataFrame(df))


def register_all(con: duckdb.DuckDBPyConnection, datasets: Dict[str, Any]) -> None:
    """
    (Ré)enregistre toutes les tables du miroir 'datasets' dans l'espace 'main'.
    - Nettoie au préalable les tables/vues existantes pour éviter collisions,
      sans toucher aux tables système.
    - N'altère PAS les noms transmis (DuckDB accepte les identifiants quotés).
    """
    # Supprime tout l'existant dans 'main' (hors système)
    existing = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    for (t,) in existing:
        con.execute(f'DROP VIEW IF EXISTS "{t}"')
        con.execute(f'DROP TABLE IF EXISTS "{t}"')

    # (Ré)enregistrement des vues avec les noms EXACTS fournis
    for name, df in (datasets or {}).items():
        _register_one(con, name, df)


# ----------------------- Exécution sécurisée ---------------------

# Liste élargie de commandes interdites : aucune modif/DDL ni commandes potentiellement sensibles.
_BANNED = (
    "DROP ", "DELETE ", "UPDATE ", "CREATE ", "ALTER ", "TRUNCATE ",
    "INSERT ", "REPLACE ", "MERGE ", "COPY ", "CALL ", "LOAD ", "EXPORT ",
    "IMPORT ", "ATTACH ", "DETACH ", "PRAGMA ", "SET ",
)

def run_query(con: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    """
    Exécute une requête de lecture (SELECT ...) avec garde-fous.
    Renvoie toujours un pandas.DataFrame.
    - Bloque DDL/DML et autres commandes non désirées.
    - L'appelant est responsable de QUOTER les noms de tables/colonnes.
    """
    q_up = (query or "").strip().upper()
    if any(tok in q_up for tok in _BANNED):
        raise ValueError("Opérations DDL/DML ou commandes interdites dans le SQL Lab.")
    return con.execute(query).df()


# ----------------------- Introspection schéma --------------------

def list_tables(con: duckdb.DuckDBPyConnection) -> List[str]:
    """
    Liste les tables/vues de l'espace 'main' triées par nom.
    Utile si l'on souhaite afficher la réalité de DuckDB plutôt que le miroir.
    """
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' ORDER BY 1"
    ).fetchall()
    return [r[0] for r in rows]


def describe_table(con: duckdb.DuckDBPyConnection, table: str) -> pd.DataFrame:
    """
    Retourne un DataFrame décrivant la table :
    - colonnes, types, nullabilité (si exposée)
    Note : utilise PRAGMA table_info('<table>').
    """
    info = con.execute(f"PRAGMA table_info('{table}')").df()

    # Normalisation des noms de colonnes pour lisibilité
    rename_map = {
        "name": "colonne",
        "type": "type",
        "notnull": "not_null",
        "dflt_value": "defaut",
        "pk": "primary_key",
    }
    for k, v in rename_map.items():
        if k in info.columns:
            info.rename(columns={k: v}, inplace=True)

    # Colonne 'nullable' (si info dispo)
    if "not_null" in info.columns:
        info["nullable"] = ~info["not_null"].astype(bool)
    elif "notnull" in info.columns:
        info["nullable"] = ~info["notnull"].astype(bool)

    # Ordre des colonnes le plus utile si présent
    ordered = [c for c in ["colonne", "type", "nullable", "primary_key", "defaut"] if c in info.columns]
    return info[ordered] if ordered else info
