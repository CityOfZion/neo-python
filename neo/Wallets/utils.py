import hashlib


def to_aes_key(password):
    """Compute/Derivate a key to be used in AES encryption from the password

    To maintain compatibility with the reference implementation the resulting
    key should be a sha256 hash of the sha256 hash of the password
    """
    password_hash = hashlib.sha256(password.encode('utf-8')).digest()
    return hashlib.sha256(password_hash).digest()
