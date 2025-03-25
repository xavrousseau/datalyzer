# EDA Explorer – FastAPI + Streamlit + Docker

Ce projet vous permet de faire une **analyse exploratoire de données (EDA)** sur n'importe quel fichier CSV, avec une interface interactive **Streamlit** et une API **FastAPI**.

---

## Fonctionnalités

- Upload de fichier CSV
- Aperçu des données (`head`)
- Valeurs manquantes (nombre + pourcentage)
- Statistiques descriptives (`describe`)
- Détection et suppression des doublons
- Suppression de colonnes
- Génération d’un rapport CSV téléchargeable
- Export du dataset nettoyé
- Graphiques interactifs avec Plotly (via Streamlit)
- Architecture Docker avec `docker-compose`

---

## Structure du projet

```
eda_explorer/
├── api/                    ← Backend FastAPI
│   ├── main.py
│   ├── test_api.py
│   └── requirements.txt
│
├── streamlit_app/          ← Interface utilisateur
│   ├── app.py
│   └── requirements.txt
│
├── data/uploads/           ← Dossiers pour fichiers CSV
│   └── test_sample.csv
│
├── Dockerfile.fastapi
├── Dockerfile.streamlit
├── docker-compose.yml
├── .dockerignore
└── README.md
```

---

## Lancement de l'application (Docker Compose)

```bash
docker-compose up --build
```

- **Streamlit** : http://localhost:8501  
- **API FastAPI (Swagger UI)** : http://localhost:8000/docs

---

## Utilisation des tests API et UI

Un jeu de données est déjà présent : `data/uploads/test_sample.csv`.

### Pour tester l'API automatiquement :

```bash
docker exec -it <nom_du_conteneur_fastapi> bash
python tests/test_api.py
```

---

## API – Endpoints disponibles

| Méthode | Endpoint             | Description |
|---------|----------------------|-------------|
| POST    | /upload/             | Upload CSV |
| GET     | /head?n=5            | Aperçu du DataFrame |
| GET     | /missing-values/     | Valeurs manquantes |
| GET     | /describe/           | Stats descriptives |
| GET     | /duplicates/         | Infos sur doublons |
| POST    | /drop-duplicates/    | Supprimer doublons |
| POST    | /drop-columns/       | Supprimer colonnes |
| GET     | /export/             | Télécharger CSV nettoyé |
| GET     | /report/             | Rapport descriptif CSV |

---

## Auteur

Projet généré automatiquement avec l’assistance de ChatGPT et Dockerisé pour un usage local ou cloud-ready.


---

## Tests Streamlit (UI)

Un test E2E est fourni avec Playwright.

### Installation des dépendances :

```bash
pip install -r tests/requirements-tests.txt
playwright install
```

### Exécution du test :

```bash
pytest tests/test_streamlit.py
```

Assurez-vous que l'interface Streamlit est en cours d'exécution à l'adresse : http://localhost:8501


---

## Fonctionnalités avancées EDA (dans Streamlit)

- 🔍 **Détection automatique des types de variables** (numérique, catégorielle, binaire)
- 📊 **Heatmap de corrélation** entre variables numériques
- 🚨 **Détection des outliers** (méthode IQR)
- 🧹 **Suggestions de nettoyage** :
  - Colonnes constantes
  - Faible variance
- 🔄 **Encodage des colonnes catégorielles** (OneHot ou Ordinal)

Accessible directement via l'interface Streamlit.


---

## Blocs EDA avancés disponibles dans l'interface

Chaque bloc est indépendant et facultatif :

- **🔍 Types de variables** : détecte automatiquement les colonnes numériques, catégorielles, binaires.
- **📊 Corrélation** : affiche une heatmap interactive entre les variables numériques.
- **🚨 Outliers (IQR)** : détecte et affiche les lignes extrêmes pour une variable numérique.
- **🧹 Suggestions nettoyage** :
  - Colonnes constantes
  - Faible variance
  - Valeurs manquantes
- **🔄 Encodage** : One-Hot ou Ordinal sur les variables sélectionnées.

Accessible directement dans l'app Streamlit (avec `st.expander()`).


---

## 📈 Visualisations interactives

- Histogrammes, boxplots, nuages de points
- Sélection dynamique des axes et des couleurs
- Affichage via **Plotly Express** intégré à l'interface Streamlit


---

## 📊 Graphiques exploratoires métiers

Inspirés du notebook original :

- Moyenne de consommation par type de bâtiment
- Moyenne d’émissions GES par type de bâtiment
- Distribution de la consommation énergétique
- Corrélation avec la consommation d'énergie

Accessibles dans la section `📊 Graphiques exploratoires métiers` de l'app Streamlit.


---

## 🎯 Sélection des variables cibles

Vous pouvez désormais choisir :
- Une **variable cible principale** (ex : consommation d'énergie)
- Une **variable secondaire** (ex : émissions GES)

Ces choix sont utilisés automatiquement dans :
- Les graphiques métiers
- Les corrélations
- Les analyses avancées

---

## ℹ️ Aides contextuelles intégrées

Chaque bloc de l'application contient désormais des **explications claires** :
- Ce qu’il fait
- Ce qu’il attend
- Comment interpréter les résultats

Idéal pour les utilisateurs non techniques.


---

## 🎨 Graphiques interactifs ajoutés

- 📦 **Boxplot interactif** : dispersion par catégorie
- 🧮 **Scatter plot** : relation entre deux variables numériques avec couleur
- 🔀 **Graphique croisé** : moyenne d’une variable cible selon deux catégories
- ✅ Les anciens graphiques métiers utilisent maintenant une **variable catégorielle sélectionnable**, pas `building_type`



---

## 📄 Rapport HTML automatique

- Généré via `ydata-profiling` (anciennement pandas-profiling)
- Contient les statistiques descriptives, distributions, corrélations, alertes, etc.
- Téléchargeable depuis l’interface

---

## 💾 Sauvegarde finale avec logs

- Le DataFrame transformé est sauvegardé au format `.parquet` dans `data/exports/`
- Un fichier `logs/eda_transformations.log` enregistre les opérations réalisées (nettoyage, encodage, etc.)
