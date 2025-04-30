## 🧰 Résumé des utilitaires de Datalyzer (`utils/`)

---

### 📁 `eda_utils.py`
**Objectif :** Fonctions pour l’analyse exploratoire des données  
**Niveau :** Avancé, riche et structuré

**Fonctions principales :**
- `detect_variable_types(df)` : Détecte les types des colonnes par heuristique.
- `summarize_dataframe(df)` : Résumé global (lignes, colonnes, NA, doublons).
- `score_data_quality(df)` : Score global qualité (NA, doublons, colonnes constantes).
- `plot_missing_values(df)` : Histogramme des valeurs manquantes.
- `detect_constant_columns(df)` : Colonnes avec une seule valeur unique.
- `detect_low_variance_columns(df, threshold)` : Colonnes numériques à faible variance.
- `detect_outliers(df, method='iqr' | 'zscore')` : Outliers avec IQR ou Z-Score.
- `detect_skewed_distributions(df)` : Colonnes avec skewness élevée.
- `compute_correlation_matrix(df)` : Matrice de corrélation Pearson.
- `get_top_correlations(df)` : Top paires les plus corrélées.
- `encode_categorical(df, cols)` : Encodage one-hot de variables catégorielles.
- `plot_boxplots(df, num, cat)` : Boxplot Num ↔ Cat.
- `compute_cramers_v_matrix(df)` : Corrélations catégorielles (Cramér’s V).

🆕 **Améliorations** :  
✔ Score global de qualité  
✔ Outliers paramétrables (méthode IQR ou Z-score)

---

### 📁 `filters.py`
**Objectif :** Sélection du fichier actif, validation d’étapes, filtrage de colonnes

**Fonctions principales :**
- `get_active_dataframe()` : Sélecteur de fichier depuis `session_state["dfs"]`.
- `validate_step_button(step)` : Affiche bouton + nom optionnel pour valider une étape.
- `mark_step_done(step, custom_name)` : Sauvegarde un snapshot et valide l’étape.
- `get_columns_by_dtype(df, dtype)` : Retourne les colonnes numériques / catégorielles / booléennes.
- `filter_dataframe_by_column(df, col, val)` : Filtre un DataFrame sur une valeur donnée.

🆕 **Amélioration** :  
✔ Message visuel si aucun fichier n’est chargé

---

### 📁 `log_utils.py`
**Objectif :** Gestion et affichage des actions utilisateur (import, suppression, erreurs…)

**Fonctions principales :**
- `log_action(type, msg)` : Enregistre un log avec horodatage dans un CSV.
- `append_log(path, headers, values)` : Log personnalisé avec entête.
- `display_log(path)` : Affiche le log dans Streamlit avec filtre par type.
- `log_error(message, context)` : Enregistre une erreur avec contexte.
- `clear_logs()` : Vide complètement le fichier de log.

🆕 **Améliorations** :  
✔ Fonction de purge  
✔ Filtrage des logs par type d’action

---

### 📁 `snapshot_utils.py`
**Objectif :** Sauvegarde / restauration de versions intermédiaires de données

**Fonctions principales :**
- `save_snapshot(df, label)` : Enregistre un CSV nommé automatiquement, avec feedback visuel.
- `list_snapshots()` : Liste tous les snapshots existants.
- `load_snapshot_by_name(name)` : Charge un snapshot spécifique.
- `load_latest_snapshot()` : Charge le plus récent automatiquement.
- `delete_snapshot(name)` : Supprime un snapshot existant.
- `get_snapshot_info(name)` : Affiche nombre de lignes et colonnes d’un snapshot.

🆕 **Améliorations** :  
✔ `st.success()` après enregistrement  
✔ Aperçu du contenu d’un snapshot via `get_snapshot_info()`

---

### 📁 `ui_utils.py`
**Objectif :** Fonctions visuelles pour l’application Streamlit

**Fonctions principales :**
- `show_header_image(image_name)` : Affiche une image stylisée avec animation (`fadein`).
- `show_icon_header(emoji, title, subtitle)` : Titre stylisé avec emoji.
- `show_eda_progress(steps_dict, status_dict)` : Barre de progression horizontale dynamique.
- `show_footer(author, github, version)` : Footer dynamique avec date du jour et version.

🆕 **Améliorations** :  
✔ Effet CSS progressif sur la bannière  
✔ Footer enrichi avec version de l’app et date

---

 