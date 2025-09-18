Presque nickel, mais il y a 4 petites incohérences avec ton code actuel :
# README 

```markdown
# 🌸 Datalyzer – Analyse exploratoire et nettoyage intelligent de données

Datalyzer est une application interactive construite avec **Streamlit** pour explorer, nettoyer, analyser et exporter vos données tabulaires. Conçue pour des analyses EDA poussées, elle offre une interface fluide et zen qui guide chaque étape du processus.

---

## 🚀 Fonctionnalités clés

- ✅ Import de fichiers CSV, TXT, Excel, Parquet
- 🧬 Détection automatique des types de variables
- 🔍 Analyse exploratoire interactive (types, valeurs manquantes, outliers, stats, corrélations…)
- 🧹 Nettoyage automatique : valeurs manquantes, colonnes constantes, faible variance
- 🧾 Correction manuelle des types (int, float, bool, datetime…)
- 💡 Suggestions de traitement (encodage, vectorisation, suppression)
- 🔗 Fusion (jointures) par clés communes
- 📈 Analyse multivariée : **ACP (PCA)**, **K-means**, projections 2D/3D
- 🎯 Analyse catégorielle : **Cramér’s V**, crosstabs normalisés, barres empilées, boxplots par modalité
- 🧪 Qualité des données (score global, heatmap, red flags)
- 💾 Export multi-format avec **sélection de colonnes** et **sous-ensemble de lignes** (filtres ET/OU, échantillon, Top-N)
- 🕰️ Snapshots (états intermédiaires) — lister, restaurer, supprimer
- 📊 Interface interactive **Plotly** + **Streamlit**

---

## 🗂️ Structure du projet

```

datalyzer/
├── app.py
├── config.py
├── sections/
│   ├── exploration.py
│   ├── typage.py
│   ├── suggestions.py
│   ├── qualite.py
│   ├── anomalies.py
│   ├── multivariee.py
│   ├── cat\_analysis.py
│   ├── cible.py
│   ├── jointures.py
│   ├── export.py
│   ├── fichiers.py
│   └── snapshots.py
│
├── utils/
│   ├── eda\_utils.py
│   ├── filters.py
│   ├── log\_utils.py
│   └── snapshot\_utils.py
│
├── data/
│   ├── snapshots/
│   └── exports/
│
├── logs/
│   └── eda\_actions.log
├── images/
├── requirements.txt
└── README.md

````

---

## ▶️ Lancement

### 1) Installer les dépendances
```bash
pip install -r requirements.txt
````

### 2) Démarrer

```bash
streamlit run app.py
```

L’app s’ouvre dans votre navigateur.

---

## 📁 Formats supportés (import)

* `.csv`
* `.txt`
* `.xlsx` / `.xls`
* `.parquet`

> Astuce CSV/TXT : détection auto du séparateur (`,` `;` `\t`).

---

## 📦 Export multi-format

* `.csv` (UTF-8, `utf-8-sig`, `latin-1`, option **gzip**)
* `.xlsx`
* `.json` (records, UTF-8, option **gzip**)
* `.parquet` (option **gzip**)

**Contrôle fin** : choisissez les **colonnes** et les **lignes** à exporter (filtres ET/OU, échantillon aléatoire, Top-N trié, déduplication, suppression des NA).
Chaque export génère un log dans `logs/eda_actions.log`.

---

## 🕰️ Snapshots

Sauvegardez l’état courant des données (après nettoyage, typage, jointure, etc.).
Tous les snapshots sont listés, prévisualisables, activables et supprimables.

---

## 🔒 Logs

Chaque action importante est journalisée dans `logs/eda_actions.log` avec :

* date/heure
* étape
* résumé

---

## 📸 Interface

* Thème Streamlit unifié
* Barre de progression des étapes EDA
* Onglets (`st.tabs`) par bloc analytique
* Visualisations interactives (histogrammes, boxplots, scatter, heatmap…)

---

## 📊 Blocs d’analyse

| Bloc             | Contenu                                                |
| ---------------- | ------------------------------------------------------ |
| **Exploration**  | Types, NA, stats, outliers, corrélations, nettoyage    |
| **Typage**       | Suggestions + corrections interactives                 |
| **Catégorielle** | **Cramér’s V**, crosstabs %, barres empilées, boxplots |
| **Multivariée**  | **ACP (PCA)**, **K-means**, projections 2D/3D          |
| **Cible**        | Analyse d’une variable à expliquer                     |
| **Jointures**    | Fusion par clés                                        |
| **Export**       | Sélection colonnes & lignes, formats, compression      |
| **Snapshots**    | Sauvegardes, chargement, suppression                   |
| **Suggestions**  | Encodage / vectorisation recommandée                   |
| **Qualité**      | Score global, heatmap, red flags                       |

---

## 🧪 Vérifications conseillées

* Import / jointures / export
* Fichiers générés dans `data/exports/`
* Snapshots dans `data/snapshots/`
* Logs dans `logs/eda_actions.log`

---

## 📌 Remarques

* Pas de base de données ni backend requis.
* Fonctionne **100 % localement**.
* Architecture modulaire (ajout de blocs & logs facile).

---

## 👤 Auteur

Conçu par **Xavier Rousseau** — Data Engineer & Analyst, passionné par la qualité des données, la visualisation et l’automatisation.

````
 
