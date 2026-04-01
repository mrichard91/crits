"""TOTP helpers compatible with the legacy CRITs secret format."""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time

from Crypto import Random
from Crypto.Cipher import AES
from django.utils.crypto import pbkdf2


def get_hotp_token(secret: bytes, intervals_no: int) -> int:
    """Calculate the HOTP token for a secret at a given interval."""

    msg = struct.pack(">Q", intervals_no)
    digest = hmac.new(secret, msg, hashlib.sha1).digest()
    offset = digest[19] & 15
    truncated = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return truncated


def decrypt_secret(secret: str | bytes, password: str, username: str) -> bytes:
    """Decrypt a stored TOTP secret using the user's PIN and username."""

    encoded_secret = secret.encode("ascii") if isinstance(secret, str) else secret
    decoded_secret = base64.b32decode(encoded_secret)
    password_hash = pbkdf2(password.encode("ascii"), username.encode("ascii"), 10000)
    cipher = AES.new(password_hash, AES.MODE_ECB)
    decrypted = cipher.decrypt(decoded_secret)
    return decrypted[:10]


def encrypt_secret(secret: bytes, password: str, username: str) -> bytes:
    """Encrypt a 10-byte TOTP secret using the legacy CRITs format."""

    padded_secret = secret + Random.new().read(6)
    password_hash = pbkdf2(password.encode("ascii"), username.encode("ascii"), 10000)
    cipher = AES.new(password_hash, AES.MODE_ECB)
    return cipher.encrypt(padded_secret)


def gen_user_secret(password: str, username: str) -> tuple[str, str]:
    """Generate encrypted and plaintext TOTP secrets for a user."""

    secret = Random.new().read(10)
    encrypted_secret = encrypt_secret(secret, password, username)
    return (
        base64.b32encode(encrypted_secret).decode("ascii"),
        base64.b32encode(secret).decode("ascii"),
    )


def valid_totp(username: str, token: str, secret: str | bytes, diff: int = 2) -> bool:
    """Validate a CRITs TOTP PIN+token combination."""

    if len(token) <= 6:
        return False

    password = token[:-6]
    try:
        current_token = int(token[-6:])
    except ValueError:
        return False

    if not secret:
        return False

    try:
        decrypted_secret = decrypt_secret(secret, password, username)
    except Exception:
        return False

    now = int(time.time()) // 30
    for interval in range(diff * -1, diff + 1):
        if get_hotp_token(decrypted_secret, now + interval) == current_token:
            return True
    return False
