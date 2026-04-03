"""crypto module - encryption and key derivation"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.exceptions import InvalidTag
import secrets
from typing import Tuple


# security config
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LENGTH = 32
ARGON2_SALT_LENGTH = 16

AES_KEY_LENGTH = 32
AES_NONCE_LENGTH = 12


class CryptoError(Exception):
    pass

class DecryptionError(CryptoError):
    pass

class KeyDerivationError(CryptoError):
    pass


def derive_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """derive encryption key from password using argon2id"""
    try:
        if salt is None:
            salt = secrets.token_bytes(ARGON2_SALT_LENGTH)
        
        if len(salt) != ARGON2_SALT_LENGTH:
            raise KeyDerivationError(f"salt must be {ARGON2_SALT_LENGTH} bytes")
        
        kdf = Argon2id(
            salt=salt,
            length=ARGON2_HASH_LENGTH,
            iterations=ARGON2_TIME_COST,
            lanes=ARGON2_PARALLELISM,
            memory_cost=ARGON2_MEMORY_COST,
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
        
    except Exception as e:
        raise KeyDerivationError(f"Key derivation failed: {e}")


def encrypt_data(data: bytes, password: str) -> bytes:
    """encrypt data with aes-256-gcm"""
    try:
        key, salt = derive_key(password)
        nonce = secrets.token_bytes(AES_NONCE_LENGTH)
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, data, associated_data=None)
        encrypted_package = salt + nonce + ciphertext
        del key
        return encrypted_package
        
    except Exception as e:
        raise CryptoError(f"Encryption failed: {e}")


def decrypt_data(encrypted_package: bytes, password: str) -> bytes:
    """decrypt data with aes-256-gcm"""
    try:
        min_size = ARGON2_SALT_LENGTH + AES_NONCE_LENGTH
        if len(encrypted_package) < min_size:
            raise DecryptionError("invalid encrypted package: too small")
        
        salt = encrypted_package[:ARGON2_SALT_LENGTH]
        nonce = encrypted_package[ARGON2_SALT_LENGTH:ARGON2_SALT_LENGTH + AES_NONCE_LENGTH]
        ciphertext = encrypted_package[ARGON2_SALT_LENGTH + AES_NONCE_LENGTH:]
        
        key, _ = derive_key(password, salt=salt)
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext, associated_data=None)
        
        del key
        return plaintext
    except InvalidTag:
        raise DecryptionError("decryption failed: incorrect password or corrupted data")
    except DecryptionError:
        raise
    except Exception as e:
        raise DecryptionError(f"decryption failed: {e}")


def verify_password_strength(password: str) -> Tuple[bool, str]:
    """check password meets minimum requirements"""
    if len(password) < 8:
        return False, "password must be at least 8 characters long"
    if len(password) < 12:
        return True, "warning: password is weak. consider using 12+ characters"
    return True, "password strength acceptable"


def calculate_encryption_overhead(data_size: int) -> int:
    """calculate total size after encryption"""
    overhead = ARGON2_SALT_LENGTH + AES_NONCE_LENGTH + 16
    return data_size + overhead


def test_encryption():
    """test crypto module functions"""
    print("=== cryptography module test ===")
    print()
    
    print("test 1: key derivation")
    password = "testpassword123"
    key1, salt = derive_key(password)
    print(f"  key: {len(key1)} bytes")
    print(f"  salt: {len(salt)} bytes")
    assert len(key1) == 32
    assert len(salt) == 16
    
    key2, _ = derive_key(password, salt=salt)
    assert key1 == key2
    print("  ✓ passed\n")
    
    print("test 2: encryption")
    test_data = b"hello, secret data"
    print(f"  original: {test_data}")
    print(f"  size: {len(test_data)} bytes")
    encrypted = encrypt_data(test_data, password)
    print(f"  encrypted: {len(encrypted)} bytes")
    print(f"  overhead: {len(encrypted) - len(test_data)} bytes")
    assert len(encrypted) > len(test_data)
    print("  ✓ passed\n")
    
    print("test 3: decryption (correct password)")
    decrypted = decrypt_data(encrypted, password)
    print(f"  decrypted: {decrypted}")
    assert decrypted == test_data
    print("  ✓ passed\n")
    
    print("test 4: decryption (wrong password)")
    try:
        decrypt_data(encrypted, "wrongpassword")
        assert False
    except DecryptionError as e:
        print(f"  correctly rejected: {e}")
        print("  ✓ passed\n")
    
    print("test 5: tampered data detection")
    corrupted = bytearray(encrypted)
    corrupted[-1] ^= 0xFF
    try:
        decrypt_data(bytes(corrupted), password)
        assert False
    except DecryptionError as e:
        print(f"  correctly rejected: {e}")
        print("  ✓ passed\n")
    
    print("test 6: large data")
    large_data = bytes(range(256)) * 100
    print(f"  testing {len(large_data)} bytes")
    encrypted = encrypt_data(large_data, password)
    decrypted = decrypt_data(encrypted, password)
    assert decrypted == large_data
    print("  ✓ passed\n")
    
    print("="*40)
    print("all tests passed ✓")
    print("="*40)
if __name__ == "__main__":
    test_encryption()
