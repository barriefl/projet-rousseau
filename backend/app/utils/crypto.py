import logging
import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def get_cipher_suite():
    """Initialise et valide la clé de chiffrement."""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "La variable 'ENCRYPTION_KEY' est introuvable dans le fichier .env ! "
            "Générez en une avec 'Fernet.generate_key().decode()'."
        )
    try:
        return Fernet(key.encode("utf-8"))
    except ValueError:
        raise ValueError(
            "La 'ENCRYPTION_KEY' n'est pas une clé Fernet valide (32 octets base64)."
        )


cipher_suite = get_cipher_suite()


def encrypt_text(text: str) -> str | None:
    """Chiffre une chaîne de caractères en AES (Fernet)."""
    if not text:
        return None

    try:
        return cipher_suite.encrypt(text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du chiffrement : {e}")
        return None


def decrypt_text(encrypted_text: str) -> str | None:
    """Déchiffre une chaîne de caractères chiffrée en AES."""
    if not encrypted_text:
        return None

    try:
        return cipher_suite.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error(
            "Erreur de chiffrement : Clé invalide ou données corrompues (InvalidToken)."
        )
        return "[Erreur : Données illisibles]"
    except Exception as e:
        logger.error(f"Erreur inattendue lors du déchiffrement : {e}")
        return "[Erreur : Déchiffrement impossible]"
