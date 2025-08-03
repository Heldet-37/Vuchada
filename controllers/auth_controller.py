from database.models import get_user_by_username, create_user
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def ensure_default_admin():
    admin = get_user_by_username("Alves37")
    if not admin:
        create_user("Alves37", hash_password("842384"), "Administrador", "admin")


def authenticate(username, password):
    user = get_user_by_username(username)
    if user:
        hashed_password = hash_password(password)
        if user[2] == hashed_password and user[5]:  # user[5] == ativo
            return user
    return None 