"""Authentication router for farmers."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import create_access_token, verify_password
from src.models.db_models import User
from src.models.schemas import FarmerInfo, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates an agricultural producer and issues a JWT token (US-01)."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas o usuario no registrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "name": user.name}
    )

    return TokenResponse(
        token_type="Bearer",
        access_token=access_token,
        expires_in=86400,
        farmer=FarmerInfo(
            id=user.id,
            name=user.name,
            cif_nif=user.cif_nif,
            regime=user.regime,
        ),
    )
