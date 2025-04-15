# utils/eda_utils.py

# =============================================================================
# 📚 IMPORTATION DES LIBRAIRIES
# =============================================================================

# Importation de pandas pour la manipulation de données sous forme de DataFrame
import pandas as pd  
# Importation de numpy pour les opérations numériques et mathématiques
import numpy as np  
# Importation des classes OneHotEncoder et OrdinalEncoder de sklearn pour encoder des variables catégorielles
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder  
# Importation de Plotly Express pour créer des graphiques interactifs
import plotly.express as px  


# =============================================================================
# 🔎 DÉTECTION DES TYPES DE VARIABLES
# =============================================================================
def detect_variable_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte automatiquement le type de chaque colonne d'un DataFrame et renvoie un résumé.
    
    Les types sont déterminés de la façon suivante :
      - Colonnes numériques : "numérique" ou "binaire" (si exactement 2 valeurs uniques)
      - Colonnes non numériques avec moins de 20 valeurs uniques : "catégorielle"
      - Autres colonnes : "texte libre"
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à analyser.
    
    Retourne:
      - pd.DataFrame
          Un DataFrame résumant le nom de la colonne, le type détecté, le dtype et le nombre de valeurs uniques.
    """
    types = []  # Liste pour stocker les informations de chaque colonne
    for col in df.columns:
        unique_vals = df[col].nunique()  # Nombre de valeurs uniques dans la colonne
        dtype = df[col].dtype  # Type de données de la colonne

        # Vérifie si la colonne est numérique
        if pd.api.types.is_numeric_dtype(df[col]):
            # Si la colonne possède exactement 2 valeurs uniques, on la considère comme binaire
            var_type = "binaire" if unique_vals == 2 else "numérique"
        # Si la colonne n'est pas numérique et a moins de 20 valeurs uniques, on la considère comme catégorielle
        elif unique_vals < 20:
            var_type = "catégorielle"
        # Sinon, on la considère comme contenant du texte libre
        else:
            var_type = "texte libre"

        # Ajoute les informations de la colonne sous forme de dictionnaire dans la liste
        types.append({
            "colonne": col,
            "type": var_type,
            "dtype": str(dtype),
            "valeurs_uniques": unique_vals
        })

    # Convertit la liste de dictionnaires en DataFrame pour un affichage structuré
    return pd.DataFrame(types)


# =============================================================================
# 🔁 MATRICE DE CORRÉLATION (PERSONNALISABLE)
# =============================================================================
def compute_correlation_matrix(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Calcule la matrice de corrélation pour les colonnes numériques du DataFrame en utilisant
    la méthode spécifiée (par défaut 'pearson').
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame contenant les données.
      - method: str, optionnel (par défaut 'pearson')
          La méthode de corrélation ('pearson', 'kendall' ou 'spearman').
    
    Retourne:
      - pd.DataFrame
          La matrice de corrélation calculée sur les colonnes numériques.
    """
    # Sélectionne uniquement les colonnes numériques
    numeric_df = df.select_dtypes(include=[np.number])
    # Calcule et retourne la matrice de corrélation avec la méthode choisie
    return numeric_df.corr(method=method)


# =============================================================================
# 🚨 DÉTECTION DES OUTLIERS PAR IQR + MARQUEUR
# =============================================================================
def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Détecte les valeurs aberrantes (outliers) dans une colonne numérique d'un DataFrame
    en utilisant la méthode de l'Intervalle Interquartile (IQR).
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame contenant les données.
      - column: str
          Le nom de la colonne sur laquelle appliquer la détection des outliers.
    
    Retourne:
      - pd.DataFrame
          Un DataFrame contenant uniquement les lignes où la valeur est considérée comme un outlier.
          Une colonne 'is_outlier' est ajoutée pour marquer ces valeurs.
    """
    # Calcul du 1er quartile (25e percentile)
    Q1 = df[column].quantile(0.25)
    # Calcul du 3e quartile (75e percentile)
    Q3 = df[column].quantile(0.75)
    # Calcul de l'intervalle interquartile
    IQR = Q3 - Q1
    # Définition des bornes inférieure et supérieure pour détecter les outliers
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    # Crée une copie du DataFrame pour éviter de modifier l'original
    result = df.copy()
    # Ajoute une colonne booléenne indiquant si la valeur est un outlier
    result["is_outlier"] = (df[column] < lower) | (df[column] > upper)
    # Retourne uniquement les lignes où 'is_outlier' est True
    return result[result["is_outlier"]]


# =============================================================================
# 📌 DÉTECTION DES COLONNES CONSTANTES
# =============================================================================
def detect_constant_columns(df: pd.DataFrame) -> list:
    """
    Identifie les colonnes du DataFrame qui contiennent une seule valeur unique 
    (y compris les valeurs manquantes).
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à analyser.
    
    Retourne:
      - list
          Une liste contenant les noms des colonnes constantes.
    """
    # Retourne les colonnes où le nombre de valeurs uniques (NaN inclus) est égal à 1
    return [col for col in df.columns if df[col].nunique(dropna=False) == 1]


# =============================================================================
# 🧮 DÉTECTION DES COLONNES À FAIBLE VARIANCE
# =============================================================================
def detect_low_variance_columns(df: pd.DataFrame, threshold: float = 0.01) -> list:
    """
    Identifie les colonnes numériques ayant une variance inférieure au seuil spécifié.
    
    Une faible variance peut indiquer que la colonne apporte peu d'information.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame contenant les données.
      - threshold: float, optionnel (par défaut 0.01)
          Le seuil de variance sous lequel une colonne est considérée comme à faible variance.
    
    Retourne:
      - list
          Une liste contenant les noms des colonnes dont la variance est inférieure au seuil.
    """
    # Sélectionne les colonnes numériques
    num_df = df.select_dtypes(include=[np.number])
    # Calcule la variance de chaque colonne numérique
    variances = num_df.var()
    # Retourne la liste des colonnes dont la variance est inférieure au seuil
    return variances[variances < threshold].index.tolist()


# =============================================================================
# 🔄 ENCODAGE DES VARIABLES CATÉGORIELLES
# =============================================================================
def encode_categorical(df: pd.DataFrame, method: str = "onehot", columns: list | None = None) -> pd.DataFrame:
    """
    Encode les variables catégorielles d'un DataFrame en utilisant soit un encodage OneHot
    (création de colonnes binaires pour chaque catégorie) soit un encodage ordinal (transformation
    en entiers ordonnés).
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame contenant les données à encoder.
      - method: str, optionnel (par défaut "onehot")
          La méthode d'encodage à utiliser. Options : "onehot" ou "ordinal".
      - columns: list ou None, optionnel
          La liste des colonnes à encoder. Si None, toutes les colonnes de type object ou category sont encodées.
    
    Retourne:
      - pd.DataFrame
          Un nouveau DataFrame avec les variables catégorielles encodées.
    
    Lève:
      - ValueError si aucune colonne catégorielle n'est trouvée ou si la méthode spécifiée est inconnue.
    """
    # Crée une copie du DataFrame pour éviter d'altérer l'original
    df = df.copy()
    
    # Si aucune liste de colonnes n'est fournie, sélectionne automatiquement toutes les colonnes de type object ou category
    if columns is None:
        columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Si aucune colonne n'est identifiée, lève une exception
    if not columns:
        raise ValueError("Aucune colonne catégorielle à encoder.")

    # Encodage OneHot : conversion en variables binaires pour chaque catégorie
    if method == "onehot":
        return pd.get_dummies(df, columns=columns)
    # Encodage ordinal : conversion en entiers ordonnés
    elif method == "ordinal":
        # Remplit les valeurs manquantes par la chaîne "manquant" pour éviter les erreurs
        df[columns] = df[columns].fillna("manquant")
        # Instanciation de l'encodeur ordinal avec gestion des inconnues (valeur -1)
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        # Application de l'encodage sur les colonnes sélectionnées
        df[columns] = encoder.fit_transform(df[columns])
        return df
    else:
        # Lève une exception si la méthode spécifiée n'est pas reconnue
        raise ValueError("Méthode d'encodage inconnue : choisir 'onehot' ou 'ordinal'")


# =============================================================================
# 📉 ANALYSE DES VALEURS MANQUANTES
# =============================================================================
def plot_missing_values(df: pd.DataFrame, seuil: float = 0.3, top_n: int = 20):
    """
    Génère un graphique interactif sous forme de barre pour visualiser le pourcentage
    de valeurs manquantes par colonne dans le DataFrame.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à analyser.
      - seuil: float, optionnel (par défaut 0.3)
          Le seuil relatif (sous forme de fraction) pour déterminer la couleur du graphique.
          Les colonnes avec un pourcentage de valeurs manquantes supérieur à (seuil*100)
          seront colorées en rouge, sinon en bleu.
      - top_n: int, optionnel (par défaut 20)
          Le nombre maximum de colonnes à afficher dans le graphique.
    
    Retourne:
      - plotly.graph_objects.Figure ou None
          Le graphique interactif généré, ou None si aucune valeur manquante n'est présente.
    """
    # Calcul du nombre total de valeurs manquantes par colonne
    missing_values = df.isnull().sum()
    # Calcul du pourcentage de valeurs manquantes par colonne
    missing_percent = (missing_values / len(df)) * 100

    # Création d'un DataFrame récapitulatif avec le nom de la colonne, le total et le pourcentage de valeurs manquantes
    missing_summary = pd.DataFrame({
        'Colonnes': df.columns,
        'Total Manquantes': missing_values,
        'Pourcentage Manquantes (%)': missing_percent
    })

    # Détermine la couleur pour chaque colonne en fonction du seuil :
    # 'red' si le pourcentage dépasse (seuil*100), sinon 'blue'
    missing_summary['Color'] = missing_summary['Pourcentage Manquantes (%)'].apply(
        lambda pct: 'red' if pct > (seuil * 100) else 'blue'
    )

    # Filtre les colonnes ayant au moins une valeur manquante
    missing_data_filtered = missing_summary[missing_summary['Total Manquantes'] > 0]
    # Trie les colonnes par pourcentage décroissant et sélectionne les top_n colonnes
    missing_data_filtered = missing_data_filtered.sort_values(by='Pourcentage Manquantes (%)', ascending=False).head(top_n)

    # Si aucune colonne avec des valeurs manquantes n'est trouvée, retourne None
    if missing_data_filtered.empty:
        return None

    # Crée un graphique à barres interactif avec Plotly Express
    fig = px.bar(
        missing_data_filtered,
        x='Colonnes',
        y='Pourcentage Manquantes (%)',
        color='Color',
        title="Pourcentage de valeurs manquantes",
        text='Pourcentage Manquantes (%)',
        color_discrete_map={'red': 'red', 'blue': 'blue'}
    )
    # Formate le texte affiché sur les barres avec deux décimales
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    # Met à jour la mise en page du graphique (fond blanc, angle des ticks de l'axe X, etc.)
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(title="Colonnes", tickangle=45),
        yaxis=dict(title="% de valeurs manquantes"),
        showlegend=False,
        height=600
    )

    # Retourne le graphique généré
    return fig


def get_columns_above_threshold(df: pd.DataFrame, seuil: float) -> list:
    """
    Identifie les colonnes dont le pourcentage de valeurs manquantes est supérieur
    ou égal au seuil spécifié.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à analyser.
      - seuil: float
          Le seuil (entre 0 et 1) pour déterminer si une colonne a trop de valeurs manquantes.
    
    Retourne:
      - list
          Une liste des colonnes dépassant le seuil de valeurs manquantes.
    """
    # Calcule la proportion de valeurs manquantes pour chaque colonne et retourne celles qui dépassent le seuil
    return df.columns[df.isna().mean() >= seuil].tolist()


def drop_missing_columns(df: pd.DataFrame, seuil: float):
    """
    Supprime les colonnes d'un DataFrame dont le pourcentage de valeurs manquantes
    est supérieur ou égal au seuil donné.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à nettoyer.
      - seuil: float
          Le seuil (entre 0 et 1) pour déterminer quelles colonnes supprimer.
    
    Retourne:
      - tuple:
          * Le DataFrame après suppression des colonnes.
          * La liste des colonnes supprimées.
    """
    # Récupère la liste des colonnes à supprimer en fonction du seuil
    cols_to_drop = get_columns_above_threshold(df, seuil)
    # Retourne le DataFrame modifié et la liste des colonnes supprimées
    return df.drop(columns=cols_to_drop), cols_to_drop


# =============================================================================
# ➕ FONCTIONS SUPPLÉMENTAIRES POUR ANALYSE AVANCÉE
# =============================================================================
def get_top_correlations(df: pd.DataFrame, target: str, top_n: int = 10) -> pd.Series:
    """
    Calcule et retourne les corrélations absolues les plus élevées d'une variable cible 
    par rapport aux autres variables numériques.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame contenant les données.
      - target: str
          Le nom de la variable cible pour laquelle calculer les corrélations.
      - top_n: int, optionnel (par défaut 10)
          Le nombre de variables les plus corrélées à retourner.
    
    Retourne:
      - pd.Series
          Une série contenant les corrélations absolues les plus élevées pour la variable cible.
    """
    return df.corr()[target].drop(target).abs().sort_values(ascending=False).head(top_n)


def detect_skewed_distributions(df: pd.DataFrame, threshold: float = 1.0) -> dict:
    """
    Identifie les distributions asymétriques parmi les colonnes numériques du DataFrame.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à analyser.
      - threshold: float, optionnel (par défaut 1.0)
          Le seuil à partir duquel une distribution est considérée comme asymétrique.
    
    Retourne:
      - dict
          Un dictionnaire où chaque clé est le nom d'une colonne et la valeur correspondante est 
          le coefficient d'asymétrie, pour les colonnes dont l'asymétrie absolue dépasse le seuil.
    """
    # Sélectionne les colonnes numériques
    num_df = df.select_dtypes(include=[np.number])
    # Calcule l'asymétrie pour chaque colonne et trie par ordre décroissant
    skewness = num_df.skew().sort_values(ascending=False)
    # Retourne sous forme de dictionnaire les colonnes dont l'asymétrie dépasse le seuil en valeur absolue
    return skewness[abs(skewness) > threshold].to_dict()


def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Génère un résumé statistique complet du DataFrame, incluant les statistiques descriptives,
    le pourcentage de valeurs manquantes et le type de données de chaque colonne.
    
    Paramètres:
      - df: pd.DataFrame
          Le DataFrame à résumer.
    
    Retourne:
      - pd.DataFrame
          Un DataFrame contenant le résumé statistique et des informations complémentaires pour chaque colonne.
    """
    # Calcule les statistiques descriptives pour toutes les colonnes et transpose le résultat pour la lisibilité
    summary = df.describe(include='all').transpose()
    # Ajoute une colonne indiquant le pourcentage de valeurs manquantes pour chaque colonne
    summary['missing (%)'] = df.isnull().mean() * 100
    # Ajoute une colonne avec le type de données de chaque colonne
    summary['dtype'] = df.dtypes
    return summary
