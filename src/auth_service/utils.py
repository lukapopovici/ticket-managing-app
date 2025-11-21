import hashlib

def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def verify_password(raw: str, hashed: str) -> bool:
    return hash_password(raw) == hashed
