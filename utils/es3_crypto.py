"""Easy Save 3 (ES3) AES encrypt/decrypt.

Algorithm (Unity ES3):
  IV   = first 16 bytes of the file
  Key  = PBKDF2-HMAC-SHA1(password, salt=IV, iterations=100, dklen=16|32)
  file = IV || AES-CBC(Key, IV).Encrypt(PKCS7(plaintext))
"""

from __future__ import annotations

import hashlib
import os
import zlib

from Crypto.Cipher import AES

DEFAULT_ITERATIONS = 100
KEY_SIZES = (16, 32)


def derive_key(
    password: str,
    iv: bytes,
    key_size: int,
    iterations: int = DEFAULT_ITERATIONS,
) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha1",
        password.encode("utf-8"),
        iv,
        iterations,
        dklen=key_size,
    )


def _pkcs7_valid(data: bytes) -> bool:
    if not data:
        return False
    pad = data[-1]
    if pad < 1 or pad > 16:
        return False
    return data[-pad:] == bytes([pad]) * pad


def _pkcs7_unpad(data: bytes) -> bytes:
    return data[: -data[-1]]


def _pkcs7_pad(data: bytes) -> bytes:
    pad = 16 - (len(data) % 16)
    return data + bytes([pad]) * pad


def try_decompress(data: bytes) -> bytes | None:
    strategies = (
        lambda d: zlib.decompress(d, -15),
        lambda d: zlib.decompress(d, 15 + 16),
        lambda d: zlib.decompress(d),
    )
    for fn in strategies:
        try:
            return fn(data)
        except Exception:  # noqa: BLE001
            continue
    return None


def decrypt_raw(data: bytes, password: str) -> tuple[bytes | None, int | None]:
    """Return (plaintext, key_size) or (None, None)."""
    if len(data) < 32:
        return None, None
    iv = data[:16]
    ct = data[16:]
    for ks in KEY_SIZES:
        key = derive_key(password, iv, ks)
        try:
            pt = AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
        except Exception:  # noqa: BLE001
            continue
        if not _pkcs7_valid(pt):
            continue
        return _pkcs7_unpad(pt), ks
    return None, None


def encrypt(
    plaintext: bytes,
    password: str,
    *,
    iv: bytes | None = None,
    key_size: int = 16,
    iterations: int = DEFAULT_ITERATIONS,
) -> bytes:
    if iv is None:
        iv = os.urandom(16)
    key = derive_key(password, iv, key_size, iterations)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(_pkcs7_pad(plaintext))


def looks_like_json(data: bytes) -> bool:
    sample = data.lstrip()[:1]
    return sample in (b"{", b"[")
