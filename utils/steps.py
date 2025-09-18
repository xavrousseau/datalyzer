# utils/steps.py
# ============================================================
# Etapes EDA — ordre unique + codes stables
# ============================================================

from collections import OrderedDict

EDA_STEPS = OrderedDict([
    ("typing",          "Types de variables"),
    ("missing",         "Valeurs manquantes"),
    ("stats",           "Statistiques descriptives"),
    ("distributions",   "Distributions"),
    ("extremes",        "Valeurs extrêmes"),
    ("correlations",    "Corrélations"),
    ("cleaning",        "Nettoyage intelligent"),
    ("anomalies",       "Anomalies"),  
    ("multivariate",    "Analyse multivariée"),
    ("categorial",      "Analyse catégorielles"),
    ("cible",           "Cible"),
    ("suggestions",      "Suggestions"),
])
