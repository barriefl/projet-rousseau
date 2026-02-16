import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

SECRET_KEY = os.getenv("ENCRYPTION_KEY")

if not SECRET_KEY:
    raise ValueError(
        "La variable 'ENCRYPTION_KEY' est introuvable dans le fichier .env ! "
        "Générez en une avec 'Fernet.generate_key().decode()'."
    )

try:
    cipher_suite = Fernet(SECRET_KEY.encode('utf-8'))
except ValueError:
    raise ValueError(
        "La 'ENCRYPTION_KEY' n'est pas une clé Fernet valide (elle doit faire 32 octets et être encodée en base 64)."
    )

def encrypt_text(text: str) -> str | None:
    """Chiffre une chaîne de caractères en AES (Fernet)."""
    if not text:
        return None
    
    try:
        return cipher_suite.encrypt(text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"Erreur inattendue lors du chiffrement : {e}")
        return None

def decrypt_text(encrypted_text: str) -> str | None:
    """Déchiffre une chaîne de caractères chiffrée en AES."""
    if not encrypted_text:
        return None
    
    try:
        return cipher_suite.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        logger.error("Erreur de chiffrement : Clé invalide ou données corrompues (InvalidToken).")
        return "[Erreur : Données illisibles]"
    except Exception as e:
        logger.error(f"Erreur inattendue lors du déchiffrement : {e}")
        return "[Erreur : Déchiffrement impossible]"