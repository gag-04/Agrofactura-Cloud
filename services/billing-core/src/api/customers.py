"""Customer and agricultural cooperative directory router."""

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import decode_access_token
from src.models.db_models import Customer, User
from src.models.schemas import CustomerCreate, CustomerResponse
from src.services.fiscal_engine import validate_spanish_id

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_current_user(
    authorization: str = Header(None), db: Session = Depends(get_db)
) -> User:
    """Dependency that authenticates current farmer via Bearer JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        # Fallback to demo farmer for developer ease if no token supplied
        demo = db.query(User).filter(User.email == "agricultor.picual@agroejemplo.es").first()
        if demo:
            return demo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere cabecera 'Authorization: Bearer <token>'",
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o expirado.",
        )

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return user


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieves directory of cooperatives and clients for current farmer (US-02)."""
    return db.query(Customer).filter(Customer.farmer_id == current_user.id).all()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registers a new buyer/cooperative, validating official Spanish NIF/CIF (US-02)."""
    if not validate_spanish_id(customer_in.cif_nif):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"El CIF/NIF '{customer_in.cif_nif}' no cumple "
                "con el algoritmo oficial español."
            ),
        )

    customer = Customer(
        farmer_id=current_user.id,
        company_name=customer_in.company_name,
        cif_nif=customer_in.cif_nif.upper(),
        email=customer_in.email,
        address=customer_in.address,
        status="active",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
