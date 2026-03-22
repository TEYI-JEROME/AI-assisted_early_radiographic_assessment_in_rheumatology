from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AuthError, ForbiddenError
from app.core.security import decode_token
from app.db.deps import get_db
from app.models.user import User


class AuthDeps:
    @staticmethod
    def require_user(request: Request, db: Session = Depends(get_db)) -> User:
        token = request.cookies.get("ra_access")
        if not token:
            raise AuthError("Not authenticated.", http_status=401)

        try:
            payload = decode_token(token)
        except Exception:
            raise AuthError("Invalid session.", http_status=401)

        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid session payload.", http_status=401)

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise AuthError("Account disabled.", http_status=401)

        return user

    @staticmethod
    def require_roles(*roles: str):
        def _dep(user: User = Depends(AuthDeps.require_user)) -> User:
            if any(user.has_role(role) for role in roles):
                return user
            raise ForbiddenError("Insufficient privileges.", http_status=403)

        return _dep