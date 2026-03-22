from datetime import datetime
from fastapi import Response
from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.models.user import User
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


class AuthService:
    def __init__(self) -> None:
        self._passwords = PasswordService()
        self._tokens = TokenService()

    def login(self, db: Session, *, email: str, password: str, response: Response) -> User:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user or not user.is_active:
            raise AuthError("Invalid credentials.", http_status=401)

        if not self._passwords.verify_password(password, user.password_hash):
            raise AuthError("Invalid credentials.", http_status=401)

        user.last_login_at = datetime.utcnow()
        db.add(user)
        db.commit()

        roles = [r.name for r in user.roles]
        access = self._tokens.create_access(user.id, roles)

        response.set_cookie(
            key="ra_access",
            value=access,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
        )

        return user

    def logout(self, response: Response) -> None:
        response.delete_cookie("ra_access", path="/")