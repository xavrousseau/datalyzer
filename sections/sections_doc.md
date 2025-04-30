## 🧰 Résumé des fichiers de Datalyzer (dossier `sections/`)

### 📁 `typage.py`
**Objectif :** Correction interactive des types des colonnes du DataFrame  
**Fonctionnalités principales :**
- **Suggestions automatiques de types** : Détecte les types de colonnes et suggère des corrections (`int`, `float`, `datetime`, `bool`, `string`).
- **Interface interactive** : L’utilisateur peut **sélectionner le type cible** pour chaque colonne.
- **Application des corrections** : Permet d'appliquer les modifications et sauvegarder un **snapshot** des données corrigées.
- **Améliorations** :  
  - **Expander** pour afficher les suggestions de typage.
  - Prévisualisation avant application des corrections.
  - **Ajout de prévisualisation** des types des colonnes et amélioration de l'expérience utilisateur.

---

### 📁 `exploration.py`
**Objectif :** Analyse exploratoire des données (types, valeurs manquantes, distributions, outliers)  
**Fonctionnalités principales :**
- **Onglets interactifs** : Permet de naviguer entre différentes analyses comme les **types de colonnes**, l’analyse des **valeurs manquantes**, des **distributions**, des **outliers**, et du **nettoyage automatique**.
- **Visualisation avec Plotly** : Histogrammes, boxplots et projections.
- **Suggestions de nettoyage** : Détecte les colonnes à supprimer (outliers, valeurs manquantes) et propose un nettoyage automatique.
- **Améliorations** :  
  - **Affichage interactif** des résultats sous forme de graphiques et de tables.
  - Prévisualisation dynamique des données.
  - Ajout de la **moyenne et médiane** pour les groupes catégoriels.
  - Options de **filtrage dynamique** pour une exploration rapide des données.

---

### 📁 `anomalies.py`
**Objectif :** Détection et gestion des anomalies (outliers via Z-score ou IQR)  
**Fonctionnalités principales :**
- **Détection d'outliers** via Z-score ou IQR.
- **Visualisation interactive** : Affichage des outliers détectés avec un histogramme et une projection graphique.
- **Sélection et suppression d'outliers** : L’utilisateur peut **sélectionner et supprimer** les outliers manuellement.
- **Analyse de l’impact** avant et après la suppression des outliers.
- **Améliorations** :  
  - Ajout d'une **évaluation de la qualité du clustering** pour les outliers.
  - Option pour **visualiser les outliers** en fonction des colonnes sélectionnées.

---

### 📁 `suggestions.py`
**Objectif :** Identifier les colonnes à encoder ou vectoriser  
**Fonctionnalités principales :**
- **Suggestions automatiques** : Identifie les colonnes catégorielles à encoder et les colonnes à vectoriser (texte libre).
- **Sélection manuelle des colonnes** : Permet de choisir manuellement les colonnes à traiter.
- **Suppression automatique des colonnes inutiles** (vectorisables).
- **Améliorations** :  
  - **Filtrage dynamique** pour les suggestions basées sur les types de données.
  - Confirmation de la **suppression des colonnes** avec aperçu des données à supprimer.
  - Option d'**exportation des résultats** pour une analyse plus approfondie.

---

### 📁 `multivariee.py`
**Objectif :** Analyse multivariée (ACP, clustering, projections)  
**Fonctionnalités principales :**
- **ACP (Analyse en Composantes Principales)** : Permet de réduire la dimensionnalité des données et de visualiser la variance expliquée par les différentes composantes.
- **Clustering KMeans** : Option d’appliquer un **clustering post-ACP** pour segmenter les données en groupes.
- **Projection 2D** des composantes principales pour une analyse visuelle.
- **Visualisation des relations entre variables** : Boxplots et nuages de points (scatter plots).
- **Améliorations** :  
  - **Filtrage des outliers** avant l’ACP et le clustering.
  - **Sélection automatique du nombre de clusters** basé sur les données.
  - **Analyse de la contribution des variables** à chaque composante principale.

---

### 📁 `cat_analysis.py`
**Objectif :** Analyse des variables catégorielles (Cramér’s V, regroupements, boxplots)  
**Fonctionnalités principales :**
- **Analyse des corrélations catégorielles** avec la méthode **Cramér’s V**.
- **Analyse des regroupements** par des variables catégorielles (moyennes par groupe).
- **Boxplots** pour visualiser les relations entre variables numériques et catégorielles.
- **Nuage de points** pour explorer les relations entre variables.
- **Améliorations** :  
  - **Filtrage dynamique** des corrélations pour ne montrer que les paires les plus significatives.
  - **Interprétation des résultats** avec des explications détaillées des matrices de Cramér’s V.

---

### 📁 `qualite.py`
**Objectif :** Évaluation de la qualité des données (score global, anomalies, doublons, placeholders)  
**Fonctionnalités principales :**
- **Score global de qualité** basé sur la présence de valeurs manquantes (NA), doublons et colonnes constantes.
- **Détection des anomalies** : Valeurs manquantes, doublons, placeholders, et outliers via Z-score.
- **Correction automatique** : Suppression des colonnes avec plus de 50% de valeurs manquantes ou constantes.
- **Visualisation de la qualité** : Carte des valeurs manquantes et résumé des anomalies détectées.
- **Améliorations** :  
  - **Amélioration de l’interprétation des résultats** avec une analyse avant/après correction des données.
  - **Options d’imputation des valeurs manquantes** pour une meilleure gestion des NA.

---

### 📁 `jointures.py`
**Objectif :** Fusion intelligente de fichiers avec suggestions de correspondances et statistiques de couverture  
**Fonctionnalités principales :**
- **Suggestions automatiques** de jointures basées sur la similarité des colonnes entre deux fichiers.
- **Sélection manuelle des colonnes à joindre** avec calcul des statistiques de correspondance.
- **Fusion des fichiers** avec différents types de jointures (inner, left, right, outer).
- **Exportation du fichier fusionné** au format CSV, avec option de téléchargement.
- **Améliorations** :  
  - **Filtrage dynamique** pour sélectionner rapidement les colonnes et corriger les erreurs de jointure.
  - **Analyse de la couverture** avant la fusion avec un aperçu des données correspondantes et non correspondantes.

---

### 📁 `home.py`
**Objectif :** Page d’accueil interactive de Datalyzer  
**Fonctionnalités principales :**
- **Présentation visuelle** de l’application avec un design épuré et zen.
- **Guide de navigation** détaillant toutes les sections principales de Datalyzer.
- **Menu latéral** pour une navigation rapide entre les différentes sections.
- **Accès direct aux fonctionnalités** telles que l’importation de fichiers, l’analyse des données, la correction de la qualité et l’exportation.
- **Améliorations** :  
  - Ajout d’un **menu latéral flottant** pour naviguer directement vers les sections importantes de l’application.

---

### 📁 `fichiers.py`
**Objectif :** Chargement multi-format de fichiers (CSV, Excel, Parquet, Texte)  
**Fonctionnalités principales :**
- **Importation de fichiers multiples** avec aperçu, résumé analytique et sélection dynamique du fichier actif.
- **Sauvegarde des snapshots** pour garder une trace des versions des fichiers importés.
- **Visualisation rapide** des fichiers importés avec possibilité de charger ou supprimer les snapshots.
- **Améliorations** :  
  - **Personnalisation du nom de snapshot** avant sauvegarde.
  - Gestion des **erreurs de chargement de fichiers** avec messages détaillés.

---

### 📁 `export.py`
**Objectif :** Export des données sélectionnées avec personnalisation du format et du nom du fichier  
**Fonctionnalités principales :**
- **Sélection des colonnes à exporter** avec possibilité d'inclure ou d'exclure l'index.
- **Export dans plusieurs formats** : CSV, Excel, JSON, Parquet, avec personnalisation du nom de fichier.
- **Sauvegarde des résultats** sous forme de snapshot.
- **Améliorations** :  
  - **Compression des fichiers Parquet** pour une meilleure gestion des volumes de données.
  - **Prévisualisation des données** avant export pour éviter les erreurs.

---

### 📝 Résumé global :
Les scripts dans le dossier **`sections/`** permettent une analyse **complète, interactive et fluide** des données à travers des étapes comme l'importation, la correction, la fusion, l'analyse multivariée et catégorielle, ainsi que l'exportation des résultats. Grâce à des visualisations avancées et des options interactives, l’utilisateur peut explorer, nettoyer et transformer ses données tout en suivant un flux logique et structuré.

---
 