# app.py

import streamlit as st

# Configuration de la page Streamlit
from config import configure_app

# Utils (depuis dossier utils/)
from utils.snapshot_utils import save_snapshot, restore_snapshot
from utils.log_utils import log_transformation

# Import des fonctions de chaque module de section
from sections.chargement import run_chargement
from sections.jointures import run_jointures
from sections.analyse_explo import run_analyse_exploratoire
from sections.analyse_cat import run_analyse_categorielle
from sections.cible import run_cible
from sections.qualite import run_qualite
from sections.multivariee import run_multivariee
from sections.snapshots import run_snapshots
from sections.export import run_export

# =============================================================================
# 🎨 INITIALISATION DE LA PAGE
# =============================================================================
configure_app()

# =============================================================================
# 🧭 MENU DE NAVIGATION
# =============================================================================
section = st.sidebar.radio("🧭 Navigation", [
    "📂 Chargement",
    "🔗 Jointures",
    "🔍 Analyse exploratoire",
    "📊 Analyse catégorielle",
    "🎯 Analyse variable cible",
    "🚨 Qualité des données",
    "🧪 Analyse multivariée",
    "🕰️ Snapshots",
    "💾 Export"
])

# =============================================================================
# 📁 ROUTAGE VERS CHAQUE SECTION
# =============================================================================

if section == "📂 Chargement":
    run_chargement()

elif section == "🕰️ Snapshots":
    run_snapshots()

else:
    # Sélection du DataFrame actif
    from utils.filters import select_active_dataframe
    df, selected_name = select_active_dataframe()

    if section == "🔗 Jointures":
        run_jointures()

    elif section == "🔍 Analyse exploratoire":
        run_analyse_exploratoire(df)

    elif section == "📊 Analyse catégorielle":
        run_analyse_categorielle(df)

    elif section == "🎯 Analyse variable cible":
        run_cible(df)

    elif section == "🚨 Qualité des données":
        run_qualite(df)

    elif section == "🧪 Analyse multivariée":
        run_multivariee(df)

    elif section == "💾 Export":
        run_export(df)
