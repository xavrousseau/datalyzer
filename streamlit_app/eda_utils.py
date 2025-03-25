# =============================================================================
# IMPORTATION DES LIBRAIRIES
# =============================================================================

# pandas est une bibliothèque essentielle pour la manipulation et l'analyse de données sous forme de DataFrame.
import pandas as pd

# numpy est utilisé pour les opérations numériques et mathématiques, notamment pour manipuler des tableaux.
import numpy as np

# sklearn.preprocessing fournit des outils pour prétraiter et encoder les données.
# - OneHotEncoder permet de convertir des variables catégorielles en variables indicatrices (dummy variables).
# - OrdinalEncoder encode les variables catégorielles sous forme d'entiers.
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

# scipy.stats propose diverses fonctions statistiques, bien que dans ce script, il n'est pas utilisé directement.
from scipy import stats


# =============================================================================
# 🔎 DÉTECTION DES TYPES DE VARIABLES
# =============================================================================
def detect_variable_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retourne un tableau (DataFrame) décrivant chaque variable du DataFrame source.
    
    Pour chaque colonne, cette fonction :
    - Calcule le nombre de valeurs uniques.
    - Identifie le type de donnée (numérique, catégorielle, binaire ou texte libre) selon :
        * Si la colonne est de type numérique, et si elle contient exactement 2 valeurs uniques, on la considère comme binaire.
        * Si la colonne est numérique mais contient plus de 2 valeurs, elle est considérée comme numérique.
        * Si la colonne n'est pas numérique et possède moins de 20 valeurs uniques, elle est considérée comme catégorielle.
        * Sinon, elle est considérée comme du texte libre.
        
    Retourne :
        Un DataFrame avec le nom de la colonne, le type détecté, le type de donnée (dtype) et le nombre de valeurs uniques.
    """
    types = []  # Liste pour stocker les informations de chaque colonne
    for col in df.columns:
        unique_vals = df[col].nunique()  # Nombre de valeurs uniques dans la colonne
        dtype = df[col].dtype  # Type de données de la colonne

        # Détection du type de variable selon le type et le nombre de valeurs uniques
        if pd.api.types.is_numeric_dtype(df[col]):
            var_type = "binaire" if unique_vals == 2 else "numérique"
        elif unique_vals < 20:
            var_type = "catégorielle"
        else:
            var_type = "texte libre"

        # Ajout des informations de la colonne dans la liste
        types.append({
            "colonne": col,
            "type": var_type,
            "dtype": str(dtype),
            "valeurs_uniques": unique_vals
        })

    # Retourne les informations sous forme de DataFrame pour une visualisation structurée
    return pd.DataFrame(types)


# =============================================================================
# 🔁 MATRICE DE CORRÉLATION
# =============================================================================
def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule et retourne la matrice de corrélation entre les variables numériques du DataFrame.
    
    Processus :
    - Sélectionne uniquement les colonnes de type numérique.
    - Utilise la méthode corr() de pandas pour calculer la corrélation entre ces colonnes.
    
    Retourne :
        Un DataFrame représentant la matrice de corrélation.
    """
    numeric_df = df.select_dtypes(include=[np.number])  # Sélection des colonnes numériques
    return numeric_df.corr()


# =============================================================================
# 🚨 DÉTECTION DES OUTLIERS PAR LA MÉTHODE IQR
# =============================================================================
def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Identifie et retourne les lignes contenant des outliers dans une colonne numérique donnée.
    
    Processus :
    - Calcule le premier (Q1) et le troisième quartile (Q3) de la colonne.
    - Détermine l'Intervalle Interquartile (IQR = Q3 - Q1).
    - Définit une plage acceptable (entre Q1 - 1.5*IQR et Q3 + 1.5*IQR).
    - Retourne les lignes dont la valeur est en dehors de cette plage.
    
    Args:
        df (pd.DataFrame): Le DataFrame source.
        column (str): Le nom de la colonne à analyser.
    
    Retourne :
        Un DataFrame contenant uniquement les lignes considérées comme outliers.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1  # Calcul de l'intervalle interquartile
    lower = Q1 - 1.5 * IQR  # Seuil inférieur
    upper = Q3 + 1.5 * IQR  # Seuil supérieur
    return df[(df[column] < lower) | (df[column] > upper)]  # Retourne les lignes en dehors des seuils


# =============================================================================
# 📌 DÉTECTION DES COLONNES CONSTANTES
# =============================================================================
def detect_constant_columns(df: pd.DataFrame) -> list:
    """
    Identifie et retourne une liste des colonnes du DataFrame qui sont constantes,
    c'est-à-dire qui ne contiennent qu'une seule valeur unique (y compris les valeurs manquantes).
    
    Retourne :
        Une liste des noms de colonnes constantes.
    """
    return [col for col in df.columns if df[col].nunique(dropna=False) == 1]


# =============================================================================
# 🧮 DÉTECTION DES COLONNES À FAIBLE VARIANCE
# =============================================================================
def detect_low_variance_columns(df: pd.DataFrame, threshold: float = 0.01) -> list:
    """
    Retourne une liste des colonnes numériques dont la variance est inférieure à un seuil donné.
    
    Processus :
    - Sélectionne les colonnes numériques.
    - Calcule la variance de chaque colonne.
    - Retourne celles dont la variance est inférieure au seuil.
    
    Args:
        df (pd.DataFrame): Le DataFrame source.
        threshold (float): Le seuil de variance sous lequel la colonne est considérée à faible variance (par défaut 0.01).
    
    Retourne :
        Une liste des noms de colonnes à faible variance.
    """
    num_df = df.select_dtypes(include=[np.number])
    variances = num_df.var()
    return variances[variances < threshold].index.tolist()


# =============================================================================
# 🔄 ENCODAGE DES VARIABLES CATÉGORIELLES
# =============================================================================
def encode_categorical(df: pd.DataFrame, method: str = "onehot", columns: list = None) -> pd.DataFrame:
    """
    Encode les colonnes catégorielles du DataFrame en utilisant l'une des méthodes suivantes : OneHot ou Ordinal.
    
    Processus :
    - Effectue une copie du DataFrame pour ne pas modifier l'original.
    - Si aucune liste de colonnes n'est fournie, détecte automatiquement les colonnes de type 'object' ou 'category'.
    - Si aucune colonne catégorielle n'est trouvée, lève une erreur.
    
    Méthodes d'encodage :
    - 'onehot' : Utilise la fonction get_dummies de pandas pour créer des colonnes indicatrices.
    - 'ordinal' : Utilise OrdinalEncoder de sklearn pour transformer les catégories en nombres entiers.
      * Les valeurs manquantes sont remplacées par la chaîne "manquant" avant encodage pour éviter les erreurs.
    
    Args:
        df (pd.DataFrame): Le DataFrame source.
        method (str): La méthode d'encodage à utiliser ('onehot' ou 'ordinal').
        columns (list): Liste des colonnes à encoder. Si None, les colonnes catégorielles sont détectées automatiquement.
    
    Retourne :
        Un nouveau DataFrame avec les colonnes spécifiées encodées.
    
    Raises:
        ValueError: Si aucune colonne catégorielle n'est trouvée ou si la méthode d'encodage est inconnue.
    """
    df = df.copy()  # Crée une copie du DataFrame pour ne pas altérer l'original

    # Détection automatique des colonnes catégorielles si aucune liste n'est spécifiée
    if columns is None:
        columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Vérifie qu'il y a des colonnes à encoder
    if not columns:
        raise ValueError("Aucune colonne catégorielle à encoder.")

    # Encodage OneHot : création de colonnes indicatrices pour chaque catégorie
    if method == "onehot":
        return pd.get_dummies(df, columns=columns)

    # Encodage Ordinal : transformation des catégories en nombres entiers
    elif method == "ordinal":
        # Remplacement des valeurs manquantes par une catégorie spéciale pour éviter des erreurs
        df[columns] = df[columns].fillna("manquant")
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        df[columns] = encoder.fit_transform(df[columns])
        return df

    else:
        raise ValueError("Méthode d'encodage inconnue : choisir 'onehot' ou 'ordinal'")
