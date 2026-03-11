import pytest

import app.utils.crypto
from app.utils.crypto import decrypt_text, encrypt_text, get_cipher_suite


# ---------------------------------------------------------
# TESTS DE FONCTIONNEMENT (SUCCESS/EMPTY).
# ---------------------------------------------------------
def test_encrypt_decrypt_integration():
    """Test du cycle complet : chiffrement puis déchiffrement."""
    # ARRANGE.
    original_text = "Secret de polichinelle"

    # ACT.
    encrypted = encrypt_text(original_text)
    decrypted = decrypt_text(encrypted)

    # ASSERT.
    assert encrypted != original_text
    assert decrypted == original_text


def test_crypto_none_or_empty():
    """Vérifie que les fonctions gèrent le None et l'input vide."""
    # ASSERT.
    assert encrypt_text(None) is None
    assert encrypt_text("") is None
    assert decrypt_text(None) is None
    assert decrypt_text("") is None


# ---------------------------------------------------------
# TESTS DE GESTION DES ERREURS (INVALID/CORRUPTED).
# ---------------------------------------------------------
def test_decrypt_invalid_token():
    """Vérifie la gestion d'un token corrompu."""
    # ACT.
    result = decrypt_text("token_completement_bidon")

    # ASSERT.
    assert result == "[Erreur : Données illisibles]"


def test_decrypt_exception(monkeypatch):
    """Force une exception générique lors du déchiffrement."""
    # ARRANGE.
    monkeypatch.setattr(app.utils.crypto.cipher_suite, "decrypt", lambda x: 1 / 0)

    # ACT.
    result = decrypt_text("un_token_quelconque")

    # ASSERT.
    assert result == "[Erreur : Déchiffrement impossible]"


def test_encrypt_exception(monkeypatch):
    """Force une exception générique lors du chiffrement."""
    # ARRANGE.
    monkeypatch.setattr(app.utils.crypto.cipher_suite, "encrypt", lambda x: 1 / 0)

    # ASSERT.
    assert encrypt_text("test") is None


# ---------------------------------------------------------
# TESTS DE CONFIGURATION (KEY VALIDATION).
# ---------------------------------------------------------
def test_get_cipher_suite_missing_key(monkeypatch):
    """Vérifie l'erreur quand la clé est absente."""
    # ARRANGE.
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

    # ACT & ASSERT.
    with pytest.raises(ValueError, match="introuvable dans le fichier .env"):
        get_cipher_suite()


def test_get_cipher_suite_invalid_key(monkeypatch):
    """Vérifie l'erreur quand la clé n'est pas au format Fernet."""
    # ARRANGE.
    monkeypatch.setenv("ENCRYPTION_KEY", "cle-trop-courte")

    # ACT & ASSERT.
    with pytest.raises(ValueError, match="pas une clé Fernet valide"):
        get_cipher_suite()
