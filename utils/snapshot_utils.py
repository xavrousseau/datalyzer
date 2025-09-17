# ============================================================
# Fichier : utils/snapshot_utils.py
# Objectif : Snapshots : sauvegarde / liste / lecture / suppression
# Choix : format unique CSV pour l’UI ; noms timestampés pour tri chronologique
# Points forts :
#   - Ecriture ATOMIQUE : on écrit dans un fichier temporaire puis os.replace()
#   - Encodage UTF-8, newline contrôlé, option compression gzip
#   - Slugify strict des labels (noms sûrs, portables)
#   - Timestamps en UTC, triables (YYYYmmdd_HHMMSS)
#   - Listage trié + utilitaires de métadonnées
# ============================================================

from __future__ import annotations

import csv
import os
import re
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


# ============================== Configuration =================================

# Répertoire des snapshots
SNAPSHOT_DIR = Path("data") / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Extension unique choisie (CSV), possibilité de .gz si compression=True
SNAP_EXT = ".csv"

# Schéma de nommage : {timestamp}_{label}[_{suffix}].csv[.gz]
# timestamp = UTC, format triable : YYYYmmdd_HHMMSS
_TS_FMT = "%Y%m%d_%H%M%S"


# ============================== Utils de nommage ===============================

def _slugify(text: str) -> str:
    """
    Transforme un texte libre en identifiant de fichier sûr :
      - retire une extension finale éventuelle (.csv/.parquet...)
      - normalise en minuscules
      - remplace caractères non [A-Za-z0-9_-] par underscore
      - compresse les underscores
    """
    text = (text or "").strip()
    text = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", text)  # retire extension finale courte
    text = text.lower()
    text = re.sub(r"[^\w\-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "snapshot"


def _timestamp_utc() -> str:
    """Horodatage UTC triable (YYYYmmdd_HHMMSS)."""
    return datetime.now(timezone.utc).strftime(_TS_FMT)


def _compose_filename(label: Optional[str], suffix: Optional[str], compressed: bool) -> str:
    """Construit le nom de fichier à partir de label/suffix + timestamp UTC."""
    base = _slugify(label) if label else "snapshot"
    if suffix:
        base = f"{base}_{_slugify(suffix)}"
    fname = f"{_timestamp_utc()}_{base}{SNAP_EXT}"
    return f"{fname}.gz" if compressed else fname


def _parse_snapshot_name(name: str) -> dict:
    """
    Extrait des infos depuis un nom de snapshot.
    Retourne un dict : {timestamp:str, label:str, suffix:str|None, compressed:bool}
    """
    compressed = name.endswith(".gz")
    stem = name[:-3] if compressed else name
    if not stem.endswith(SNAP_EXT):
        return {"timestamp": "", "label": "", "suffix": None, "compressed": compressed}
    stem = stem[: -len(SNAP_EXT)]  # retire .csv
    # pattern : 20250131_235959_label[_suffix]
    m = re.match(r"^(\d{8}_\d{6})_(.+)$", stem)
    if not m:
        return {"timestamp": "", "label": stem, "suffix": None, "compressed": compressed}
    ts, rest = m.groups()
    parts = rest.split("_")
    if len(parts) >= 2:
        return {
            "timestamp": ts,
            "label": "_".join(parts[:-1]),
            "suffix": parts[-1],
            "compressed": compressed,
        }
    return {"timestamp": ts, "label": rest, "suffix": None, "compressed": compressed}


# ============================== Métadonnées ===================================

@dataclass(frozen=True)
class SnapshotInfo:
    name: str                 # nom de fichier (ex: 20250131_235959_sales_clean.csv)
    path: Path
    timestamp: str            # "YYYYmmdd_HHMMSS" (UTC)
    label: str
    suffix: Optional[str]
    compressed: bool
    size_bytes: int
    rows: Optional[int] = None
    cols: Optional[int] = None

    @property
    def dt_utc(self) -> Optional[datetime]:
        try:
            return datetime.strptime(self.timestamp, _TS_FMT).replace(tzinfo=timezone.utc)
        except Exception:
            return None


def _safe_shape_from_csv(path: Path, nrows: int = 1000) -> tuple[int, int] | tuple[None, None]:
    """
    Essaie de récupérer rapidement une idée des dimensions :
      - lit au plus 'nrows' lignes pour l'échantillon
      - infère le séparateur (csv.Sniffer) avec fallback ','
    Retourne (rows_est, cols) OU (None, None) si échec.
    """
    try:
        # Détection séparateur sur un petit échantillon
        sample = path.read_bytes()[: 64 * 1024]  # 64KB
        try:
            dialect = csv.Sniffer().sniff(sample.decode("utf-8", errors="ignore"))
            sep = dialect.delimiter
        except Exception:
            sep = ","

        df = pd.read_csv(path, sep=sep, nrows=nrows, encoding="utf-8")
        # cols exact, lignes estimées si fichier > nrows (meilleur que rien)
        cols = df.shape[1]
        # estimation grossière : taille totale / taille sample * nrows (trop optimiste)
        # -> on préfère ne pas deviner et laisser None pour rows si trop approximatif
        return (None, cols)
    except Exception:
        return (None, None)


# ============================== API Snapshots =================================

def save_snapshot(
    df: pd.DataFrame,
    label: Optional[str] = None,
    suffix: Optional[str] = None,
    *,
    compressed: bool = False,
    index: bool = False,
    float_format: Optional[str] = None,
) -> str:
    """
    Sauvegarde un DataFrame en CSV (optionnellement gzip), écriture atomique.

    Nom de fichier : {timestampUTC}_{label}[_suffix].csv[.gz]
    Retour : chemin absolu (str).

    Args:
        df: DataFrame à sauvegarder.
        label: libellé logique (ex. 'ventes_nettoyees').
        suffix: suffixe optionnel (ex. 'v2', 'sample').
        compressed: True -> écrit .csv.gz (gzip niveau défaut).
        index: inclure l'index pandas (False par défaut).
        float_format: formatage des flottants, ex. '%.6g'.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    filename = _compose_filename(label, suffix, compressed)
    dest = SNAPSHOT_DIR / filename

    # Ecriture atomique : on écrit dans un fichier temporaire dans le même dossier,
    # puis os.replace() (renommage atomique sur la plupart des FS).
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=str(SNAPSHOT_DIR))
    os.close(tmp_fd)  # on fermera via pandas
    tmp = Path(tmp_path)

    try:
        if compressed:
            df.to_csv(
                tmp,
                index=index,
                encoding="utf-8",
                float_format=float_format,
                compression="gzip",
            )
        else:
            df.to_csv(
                tmp,
                index=index,
                encoding="utf-8",
                float_format=float_format,
                lineterminator="\n",
            )
        os.replace(tmp, dest)  # atomique
    except Exception:
        # On essaie de nettoyer le temp si l’écriture échoue
        with contextlib.suppress(Exception):
            tmp.unlink(missing_ok=True)
        raise

    return str(dest.resolve())


def list_snapshots() -> List[str]:
    """
    Liste les fichiers snapshots (CSV et CSV.GZ) triés du plus récent au plus ancien.
    Tri sur le nom (timestamp en préfixe → tri chronologique).
    """
    if not SNAPSHOT_DIR.is_dir():
        return []
    items = [p.name for p in SNAPSHOT_DIR.iterdir() if p.is_file() and p.name.lower().endswith((".csv", ".csv.gz"))]
    # tri décroissant (plus récent d'abord)
    items.sort(reverse=True)
    return items


def list_snapshot_info(with_shape: bool = False) -> List[SnapshotInfo]:
    """
    Version enrichie : retourne des objets SnapshotInfo (avec taille, timestamp, etc.).
    with_shape=True tente d’estimer le nombre de colonnes (rapide), lignes = None.
    """
    infos: List[SnapshotInfo] = []
    for name in list_snapshots():
        path = SNAPSHOT_DIR / name
        meta = _parse_snapshot_name(name)
        rows = cols = None
        if with_shape:
            rows, cols = _safe_shape_from_csv(path)
        infos.append(
            SnapshotInfo(
                name=name,
                path=path,
                timestamp=meta["timestamp"],
                label=meta["label"],
                suffix=meta["suffix"],
                compressed=meta["compressed"],
                size_bytes=path.stat().st_size,
                rows=rows,
                cols=cols,
            )
        )
    return infos


def load_snapshot_by_name(name: str) -> pd.DataFrame:
    """
    Charge un snapshot par son NOM DE FICHIER exact (CSV/CSV.GZ).
    Détecte le séparateur si possible, fallback ','.
    """
    path = SNAPSHOT_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Snapshot introuvable : {name}")

    # Détection simple du séparateur via csv.Sniffer (sur 64KB), sinon ','
    try:
        sample = path.read_bytes()[: 64 * 1024]
        dialect = csv.Sniffer().sniff(sample.decode("utf-8", errors="ignore"))
        sep = dialect.delimiter
    except Exception:
        sep = ","

    return pd.read_csv(path, sep=sep, encoding="utf-8")


def load_latest_snapshot() -> pd.DataFrame:
    """
    Charge le snapshot le plus récent (selon l’ordre de list_snapshots()).
    Lève FileNotFoundError si aucun.
    """
    snaps = list_snapshots()
    if not snaps:
        raise FileNotFoundError("Aucun snapshot disponible.")
    return load_snapshot_by_name(snaps[0])  # 0 = plus récent (tri desc)


def delete_snapshot(name: str) -> None:
    """
    Supprime un snapshot par son nom de fichier (silencieux si absent).
    """
    path = SNAPSHOT_DIR / name
    try:
        path.unlink(missing_ok=True)
    except TypeError:
        # Python < 3.8 : pas de missing_ok -> on catch FileNotFoundError
        try:
            path.unlink()
        except FileNotFoundError:
            pass


# ============================== Fonctions bonus ================================

def cleanup_old_snapshots(keep: int = 20) -> List[str]:
    """
    Garde les 'keep' plus récents, supprime le reste.
    Retourne la liste des noms supprimés.
    """
    snaps = list_snapshots()
    to_delete = snaps[keep:]
    for name in to_delete:
        delete_snapshot(name)
    return to_delete


def find_snapshots_by_label(label_substring: str) -> List[str]:
    """
    Recherche simple par sous-chaîne (dans la partie label/suffix du nom).
    Utile pour filtrer rapidement les versions d’un même fichier logique.
    """
    label_substring = _slugify(label_substring)
    out: List[str] = []
    for name in list_snapshots():
        meta = _parse_snapshot_name(name)
        hay = f"{meta.get('label','')}_{meta.get('suffix') or ''}"
        if label_substring in hay:
            out.append(name)
    return out
