from passlib.context import CryptContext


class PasswordService:
    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return self._ctx.verify(password, password_hash)
        except Exception:
            return False