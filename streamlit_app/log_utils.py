# =============================================================================
# IMPORTATION DES LIBRAIRIES
# =============================================================================

# loguru est une bibliothèque de logging flexible et facile à utiliser.
# Elle permet de configurer rapidement un système de journalisation (logging) avec de nombreuses options.
from loguru import logger

# pathlib fournit des classes pour manipuler les chemins de fichiers de manière orientée objet.
from pathlib import Path


# =============================================================================
# CONFIGURATION DU FICHIER DE LOG
# =============================================================================

# Définition du chemin du fichier de log sous forme d'objet Path.
# Ici, le fichier de log sera stocké dans le dossier "logs" avec le nom "eda_transformations.log".
LOG_PATH = Path("logs/eda_transformations.log")

# Création du dossier parent (ici "logs") s'il n'existe pas déjà.
# L'argument parents=True permet de créer tous les dossiers intermédiaires nécessaires.
# L'argument exist_ok=True évite une erreur si le dossier existe déjà.
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


# =============================================================================
# CONFIGURATION DU LOGGER AVEC LOGURU
# =============================================================================

# Configuration du logger pour écrire les logs dans le fichier défini.
logger.add(
    str(LOG_PATH),  # Chemin du fichier de log converti en chaîne de caractères.
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",  # Format d'affichage des logs.
    level="INFO",  # Niveau minimal de log à enregistrer (INFO et supérieur).
    rotation="1 week",            # Rotation : un nouveau fichier de log est créé chaque semaine.
    retention="4 weeks",          # Rétention : les fichiers de log plus anciens que 4 semaines sont supprimés.
    compression="zip",            # Compression : les anciens fichiers de log sont compressés au format zip.
    encoding="utf-8"              # Encodage du fichier de log.
)


# =============================================================================
# FONCTION DE LOGGING DES TRANSFORMATIONS
# =============================================================================

def log_transformation(message: str):
    """
    Enregistre un message dans le fichier de log des transformations EDA.
    
    Args:
        message (str): Le message à enregistrer dans le log.
    """
    # Utilisation de logger.info pour enregistrer le message avec le niveau INFO.
    logger.info(message)
