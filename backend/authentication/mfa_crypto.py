import os

from cryptography.fernet import Fernet, InvalidToken


class MFAEncryptionError(Exception):
    """Error seguro al cifrar o descifrar secretos MFA."""


def _get_fernet():
    key = os.environ.get("MFA_ENCRYPTION_KEY")

    if not key:
        raise MFAEncryptionError(
            "Falta configurar la variable MFA_ENCRYPTION_KEY."
        )

    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        raise MFAEncryptionError(
            "MFA_ENCRYPTION_KEY no tiene un formato válido."
        ) from None


def encrypt_totp_secret(secret: str) -> str:
    if not secret:
        raise MFAEncryptionError("El secreto TOTP está vacío.")

    try:
        return _get_fernet().encrypt(
            secret.encode("utf-8")
        ).decode("ascii")
    except MFAEncryptionError:
        raise
    except Exception:
        raise MFAEncryptionError(
            "No se pudo cifrar el secreto TOTP."
        ) from None


def decrypt_totp_secret(encrypted_secret: str) -> str:
    if not encrypted_secret:
        raise MFAEncryptionError(
            "No hay un secreto TOTP almacenado."
        )

    try:
        decrypted = _get_fernet().decrypt(
            encrypted_secret.encode("ascii")
        )
        return decrypted.decode("utf-8")
    except MFAEncryptionError:
        raise
    except (InvalidToken, ValueError, UnicodeEncodeError, UnicodeDecodeError):
        raise MFAEncryptionError(
            "No se pudo descifrar el secreto TOTP."
        ) from None
