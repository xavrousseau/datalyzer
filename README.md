# 🌸 Datalyzer – Analyse exploratoire et nettoyage intelligent de données

**Datalyzer** est une application interactive construite avec **Streamlit** qui transforme vos données tabulaires (CSV, Excel, Parquet) en une expérience d’exploration fluide, pédagogique et esthétique.
Elle guide chaque étape de l’**analyse exploratoire des données (EDA)** : import, exploration, nettoyage, typage, détection d’anomalies, évaluation de la qualité, analyses multivariées et export final.

Conçue pour les **data analysts, data scientists et ingénieurs data**, Datalyzer associe :

* une **interface intuitive** pour explorer sans coder,
* des **outils robustes** pour fiabiliser les jeux de données,
* des **visualisations interactives** pour comprendre rapidement vos variables et leurs relations.

---

## 🚀 Fonctionnalités principales

* ✅ **Import intelligent** : CSV, TXT, Excel, Parquet (séparateur auto pour CSV/TXT).
* 🧬 **Typage automatique et manuel** : détection de types + correction interactive (int, float, bool, date, cat, texte).
* 🔍 **Exploration guidée** : stats descriptives, valeurs manquantes, distributions, outliers, corrélations.
* 🧹 **Nettoyage rapide** : suppression NA, colonnes constantes, faible variance, normalisation.
* 🧪 **Qualité des données** : score global sur 100 + drapeaux (NA, doublons, placeholders, constantes).
* 🚨 **Détection d’anomalies** : méthodes robustes (Z-score, IQR, MAD).
* 🎯 **Analyse catégorielle** : matrice de Cramér’s V, crosstabs normalisés, barres empilées, boxplots.
* 📊 **Analyse cible** : relations entre une variable cible numérique et le reste du dataset (corrélations, boxplots par catégorie).
* 📈 **Multivariée** : ACP (PCA), clustering K-means, variance expliquée, projections 2D.
* 🔗 **Jointures intelligentes** : suggestions de clés, alignement automatique des types, indicateurs de couverture.
* 💾 **Export avancé** : sélection colonnes + filtres de lignes (ET/OU, top-N, échantillon, dédup, suppression NA).
* 🕰️ **Snapshots** : sauvegardez l’état intermédiaire de vos données, restaurez ou supprimez-les facilement.

---

## 📸 Aperçus

*(placeholders à remplacer par tes captures réelles)*

* Import et aperçu des données
  ![Import](docs/screenshot_import.png)

* Exploration et corrélations interactives
  ![Exploration](docs/screenshot_exploration.png)

* Score de qualité des données
  ![Qualité](docs/screenshot_quality.png)

* Export propre et traçabilité
  ![Export](docs/screenshot_export.png)

---

## ▶️ Installation et lancement

1. Installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Démarrer l’application :

```bash
streamlit run app.py
```

3. Accéder à l’interface depuis votre navigateur :
   [http://localhost:8501](http://localhost:8501)

---

## 📂 Organisation du projet

* `sections/` : pages fonctionnelles (exploration, typage, qualité, anomalies, cible, jointures, multivariée, export, snapshots)
* `utils/` : fonctions transverses (EDA, filtres, snapshots, logs, gestion de session)
* `data/` : snapshots et exports générés
* `logs/` : historique des actions utilisateur (`history_log.csv`)
* `images/` : visuels de l’interface

---

## 📌 Pourquoi utiliser Datalyzer ?

* Tout fonctionne **100 % localement**, vos données restent chez vous.
* Une **interface interactive** qui rend l’EDA accessible sans écrire de code.
* Une **traçabilité complète** : snapshots et logs pour rejouer vos étapes.
* Un **outil modulaire** pensé pour évoluer : facile à enrichir avec de nouveaux blocs analytiques.
* Un design **sobre et zen**, pour travailler efficacement sans surcharge visuelle.

---

## 👤 Auteur

Projet conçu et développé par **Xavier Rousseau**
📊 Data Engineer & Analyst — passionné par la qualité des données, la visualisation et l’automatisation.
