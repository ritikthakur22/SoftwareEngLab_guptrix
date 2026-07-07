from encryptionService import encryptionService


def test_encrypt_decrypt_round_trip():
    service = encryptionService("my-key")

    encrypted = service.encrypt("hello world")
    decrypted = service.decrypt(encrypted)

    assert encrypted != "hello world"
    assert decrypted == "hello world"
