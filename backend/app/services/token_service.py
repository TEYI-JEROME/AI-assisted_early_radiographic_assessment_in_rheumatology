from app.core.security import create_access_token, decode_token


class TokenService:
    def create_access(self, user_id: str, roles: list[str]) -> str:
        return create_access_token(user_id=user_id, roles=roles)

    def decode(self, token: str) -> dict:
        return decode_token(token)