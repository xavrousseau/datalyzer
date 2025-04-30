Parfait, voici un **README complet et professionnel** pour ton projet **Datalyzer**, en mode 100 % Streamlit, fusionnant intelligemment le fond de ton ancien README avec la structure claire de la nouvelle version. Ce document est conçu pour une présentation sérieuse, claire et réutilisable sur GitHub ou en démo client.

---

# 🌸 Datalyzer – Analyse exploratoire et nettoyage intelligent de données

Datalyzer est une application interactive construite avec **Streamlit** pour explorer, nettoyer, analyser et exporter vos données tabulaires (CSV, Excel, etc.). Conçue pour des analyses EDA poussées, elle offre une interface fluide et zen qui guide chaque étape du processus.

---

## 🚀 Fonctionnalités clés

- ✅ Import de fichiers CSV ou Excel
- 🧬 Détection automatique des types de variables
- 🔍 Analyse exploratoire interactive (types, valeurs manquantes, outliers, stats...)
- 🧹 Nettoyage automatique : valeurs manquantes, colonnes constantes, faible variance
- 🧾 Correction manuelle des types (int, float, bool, datetime...)
- 💡 Suggestions de traitement (encodage, vectorisation, suppression)
- 🔗 Fusion intelligente de fichiers par clés communes
- 📈 Analyse multivariée (ACP, clustering, corrélations)
- 🎯 Analyse ciblée avec croisement variable cible / explicative
- 🧪 Évaluation de la qualité des données (score global, heatmap, red flags)
- 💾 Export des données nettoyées dans plusieurs formats (CSV, XLSX, JSON, Parquet)
- 🕰️ Gestion complète des snapshots (états intermédiaires)
- 📊 Interface interactive avec **Plotly**, entièrement pilotée depuis **Streamlit**

---

## 🗂️ Structure du projet

```
datalyzer/
├── app.py                  ← Application principale (navigation Streamlit)
├── config.py               ← Configuration graphique & thème
├── sections/               ← Modules fonctionnels de l'application
│   ├── exploration.py
│   ├── typage.py
│   ├── suggestions.py
│   ├── qualite.py
│   ├── anomalies.py
│   ├── multivariee.py
│   ├── cat_analysis.py
│   ├── cible.py
│   ├── jointures.py
│   ├── export.py
│   ├── fichiers.py
│   └── snapshots.py
│
├── utils/                  ← Fonctions utilitaires
│   ├── eda_utils.py
│   ├── filters.py
│   ├── log_utils.py
│   └── snapshot_utils.py
│
├── data/                   ← Dossiers pour sauvegardes et exports
│   ├── snapshots/
│   └── exports/
│
├── images/                 ← Illustrations et fonds de page
├── requirements.txt        ← Dépendances Python
└── README.md               ← Ce fichier
```

---

## ▶️ Lancement de l'application

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Démarrage de l'application

```bash
streamlit run app.py
```

L'application s’ouvre automatiquement dans votre navigateur par défaut.

---

## 📁 Formats supportés

- `.csv` (standard)
- `.xlsx` (Excel)
- `.json` (en ligne ou objet)
- `.parquet` (colonnes compressées, recommandé)

---

## 📦 Export multi-format

À tout moment, vous pouvez exporter le fichier nettoyé :
- en `.csv` classique
- en `.xlsx` (Excel)
- en `.json` formaté
- en `.parquet` (optimisé pour la taille)

Un **log d’action** est généré à chaque export dans `logs/`.

---

## 🕰️ Snapshots intelligents

Chaque transformation (filtrage, nettoyage, typage, jointure...) peut être **sauvegardée** sous forme de snapshot. Ces snapshots sont listés, restaurables et supprimables à volonté depuis l’interface.

---

## 🔒 Logs automatiques

Chaque action utilisateur déclenche un **log** dans `logs/eda_actions.log`, incluant :

- Date/heure
- Étape
- Résumé de la transformation

---

## 📸 Interface graphique enrichie

Datalyzer utilise **Streamlit + Plotly** avec :

- Thème adaptatif et fluide
- Progression dynamique des étapes
- Menu latéral personnalisé
- Affichage par onglets (`st.tabs`)
- Visualisation interactive (histogrammes, boxplots, scatter, heatmap...)

---

## 📊 Blocs d’analyse disponibles

| Bloc | Contenu |
|------|---------|
| **Exploration** | Types, NA, stats, outliers, nettoyage |
| **Typage** | Suggestions + correction |
| **Suggestions** | Encodage / vectorisation recommandée |
| **Qualité** | Score, heatmap, vérifications critiques |
| **Multivariée** | ACP, clustering, projection, Cramér’s V |
| **Catégorielle** | Boxplots, croisement de modalités |
| **Cible** | Analyse ciblée d'une variable à expliquer |
| **Jointures** | Fusion intelligente de fichiers |
| **Export** | Sélection, format, téléchargement |
| **Snapshots** | Sauvegardes, chargement, suppression |

---

## 🎨 Thème & Design

- Couleurs pastel inspirées du Japon zen
- Illustrations pour chaque bloc (fond personnalisé)
- Animation douce & feedback visuel
- Icônes et emojis pour une navigation intuitive

---

## 🧪 Tests recommandés

- Vérifiez l’import, les jointures et les exports manuellement
- Vérifiez les logs dans `logs/eda_actions.log`
- Vérifiez la création automatique de `snapshots/` et `exports/`

---

## 📌 Remarques

- Le projet ne nécessite **aucune base de données ni backend**.
- L'application fonctionne **100 % localement**, sans connexion externe.
- L’architecture est **modulaire et extensible** (ajout de blocs, logs, logs visuels, plugins...).

---

## 👤 Auteur

Ce projet est une initiative personnelle conçue par **Xavier Rousseau**, Data Engineer & Analyst, passionné de qualité des données, visualisation et automatisation.

 