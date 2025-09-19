# 🌸 Datalyzer – Analyse exploratoire et nettoyage intelligent de données

**Datalyzer** est une application interactive construite avec **Streamlit** pour explorer, nettoyer et analyser vos données tabulaires (CSV, Excel, Parquet).
Pensée pour des **analyses EDA (Exploratory Data Analysis)** complètes, elle associe **interface fluide**, **visualisations interactives** et **garde-fous intelligents**.

---

## 🚀 Fonctionnalités

* ✅ Import simple (CSV, TXT, Excel, Parquet)
* 🧬 Détection et correction des types de variables
* 🔍 Exploration guidée : stats, valeurs manquantes, distributions, corrélations
* 🧹 Nettoyage intelligent : NA, colonnes constantes, faible variance
* 💡 Suggestions automatiques : encodage, vectorisation, exclusions
* 🧪 Score de qualité des données avec drapeaux
* 🚨 Détection d’anomalies (Z-score, IQR, MAD)
* 🎯 Analyses catégorielles (Cramér’s V, crosstabs, boxplots)
* 📈 Analyses multivariées (ACP, K-means, projections 2D)
* 🔗 Jointures intelligentes avec vérifications et métriques
* 💾 Export enrichi : colonnes & lignes filtrées, CSV/XLSX/Parquet, compression, logs
* 🕰️ Snapshots d’états intermédiaires, restaurables à tout moment

---

## 📸 Aperçus

*(captures d’écran à insérer ici : import, exploration, qualité, export)*

![Exploration](docs/screenshot_exploration.png)
![Qualité des données](docs/screenshot_quality.png)
![Export](docs/screenshot_export.png)

---

## ▶️ Installation

1. Créer un environnement virtuel et installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Lancer l’application :

```bash
streamlit run app.py
```

---

## 📂 Organisation

* `sections/` : pages fonctionnelles (exploration, typage, qualité, anomalies, cible, jointures, multivariée, export)
* `utils/` : fonctions transverses (EDA, snapshots, logs, gestion de session)
* `data/` : snapshots et exports
* `logs/` : historique des actions utilisateur

---

## 📌 Pourquoi l’utiliser ?

* Tout fonctionne **localement** (aucune donnée transmise en ligne).
* Une **interface pédagogique** qui rend l’EDA accessible sans code.
* Une **architecture modulaire** pensée pour évoluer (ajout facile de blocs analytiques).
* Un outil qui met la **qualité des données** au cœur de l’analyse.

---

## 👤 Auteur

Projet conçu et développé par **Xavier Rousseau**
📊 Data Engineer & Analyst | Passionné par la qualité des données, la visualisation et l’automatisation.

 