# =============================================================================
# 📚 IMPORTATION DES LIBRAIRIES
# =============================================================================

# Loguru : bibliothèque de logging facilitant la gestion des logs avec des fonctionnalités avancées
from loguru import logger  
# Pathlib : permet de manipuler facilement les chemins de fichiers de manière orientée objet
from pathlib import Path    
# Pandas : bibliothèque pour la manipulation et l'analyse des données sous forme de DataFrame
import pandas as pd         


# =============================================================================
# 📁 CONFIGURATION DU FICHIER DE LOG
# =============================================================================

# Définition du chemin du fichier de log dans le dossier "logs" avec le nom "eda_transformations.log"
LOG_PATH = Path("logs/eda_transformations.log")
# Création du dossier parent s'il n'existe pas déjà (avec tous les dossiers nécessaires)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Configuration de Loguru pour enregistrer les logs dans le fichier spécifié
logger.add(
    str(LOG_PATH),  # Convertit le chemin en chaîne de caractères pour Loguru
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",  # Format d'affichage de chaque entrée de log
    level="INFO",         # Niveau minimum des messages à enregistrer (ex: INFO, WARNING, ERROR, etc.)
    rotation="1 week",    # Rotation du fichier de log toutes les semaines (les logs anciens sont archivés)
    retention="4 weeks",  # Conservation des fichiers de log pendant 4 semaines maximum
    compression="zip",    # Compression des anciens fichiers de log au format ZIP pour économiser de l'espace disque
    encoding="utf-8"      # Encodage utilisé pour le fichier de log
)


# =============================================================================
# 📝 ENREGISTREMENT D'UNE TRANSFORMATION
# =============================================================================

def log_transformation(message: str, level: str = "info"):
    """
    Enregistre un message de transformation dans le fichier de log.
    
    Cette fonction permet d'ajouter une entrée dans le fichier de log pour suivre 
    les transformations ou modifications effectuées sur les données durant l'analyse.
    
    Args:
        message (str): Le message décrivant la transformation effectuée.
        level (str): Le niveau de log à utiliser ('info', 'warning', 'error', etc.). Par défaut "info".
    
    Exemple:
        log_transformation("Suppression des doublons effectuée.")
    """
    # Utilise getattr pour appeler dynamiquement la méthode de log correspondant au niveau spécifié (e.g., logger.info, logger.error)
    getattr(logger, level)(message)


# =============================================================================
# 📄 AFFICHAGE DES DERNIERS LOGS
# =============================================================================

def display_logs(n: int = 10) -> pd.DataFrame:
    """
    Charge et affiche les derniers logs depuis le fichier de log (non compressé).

    Cette fonction lit le fichier de log et retourne les 'n' dernières entrées sous forme de DataFrame.
    En cas d'erreur lors de la lecture, un message d'erreur est logué et un DataFrame vide est retourné.

    Args:
        n (int): Nombre de lignes de log à afficher. Par défaut, 10.

    Returns:
        pd.DataFrame: Un DataFrame contenant les dernières entrées de log avec les colonnes "date", "niveau" et "message".
    """
    try:
        # Lecture du fichier de log en spécifiant le séparateur '|' et en attribuant des noms aux colonnes
        df = pd.read_csv(LOG_PATH, sep="|", header=None, names=["date", "niveau", "message"])
        # Retourne les 'n' dernières lignes du DataFrame
        return df.tail(n)
    except Exception as e:
        # En cas d'erreur, log l'erreur et retourne un DataFrame vide avec les colonnes attendues
        logger.error(f"Erreur lors du chargement des logs : {e}")
        return pd.DataFrame(columns=["date", "niveau", "message"])


# =============================================================================
# 🔍 LOG DES DIMENSIONS D'UN DATAFRAME
# =============================================================================

def log_dataframe_shape(df: pd.DataFrame, step: str):
    """
    Log la forme (dimensions) d'un DataFrame à une étape précise du traitement.

    Cette fonction permet d'enregistrer dans le log le nombre de lignes et de colonnes d'un DataFrame,
    afin de suivre les changements apportés lors des différentes étapes de transformation des données.

    Args:
        df (pd.DataFrame): Le DataFrame à analyser.
        step (str): Description de l'étape (exemple : "Après nettoyage", "Après suppression des doublons").

    Exemple:
        log_dataframe_shape(dataframe, "Après suppression des colonnes manquantes")
    """
    # Création du message indiquant le nombre de lignes et de colonnes du DataFrame à l'étape donnée
    message = f"{step} → {df.shape[0]} lignes, {df.shape[1]} colonnes"
    # Enregistre le message avec le niveau INFO dans le fichier de log
    logger.info(message)
