#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import hashlib

class encryptionService:
    def __init__(self, key):
        if not key:
            raise ValueError("Encryption key must not be empty")
        self._key_bytes = hashlib.sha256(key.encode("utf-8")).digest()

    def _xor_bytes(self, payload):
        return bytes(
            byte ^ self._key_bytes[index % len(self._key_bytes)]
            for index, byte in enumerate(payload)
        )

    def encrypt(self, plaintext):
        raw = plaintext.encode("utf-8")
        encrypted = self._xor_bytes(raw)
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    def decrypt(self, ciphertext):
        encrypted = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
        raw = self._xor_bytes(encrypted)
        return raw.decode("utf-8")
