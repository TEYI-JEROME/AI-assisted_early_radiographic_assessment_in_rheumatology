from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.auth import LoginRequest, MeResponse
from app.services.admin_service import AuthDeps
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=MeResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> MeResponse:
    svc = AuthService()
    user = svc.login(db, email=payload.email, password=payload.password, response=response)

    return MeResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
    )


@router.post("/logout")
def logout(response: Response) -> dict:
    AuthService().logout(response)
    return {"status": "ok"}


@router.get("/me", response_model=MeResponse)
def me(user=Depends(AuthDeps.require_user)) -> MeResponse:
    return MeResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
    )