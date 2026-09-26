# Client endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user, require_active_client, require_verified_email
from app.clients.schemas import ClientRegister, ClientResponse, ClientUpdate
from app.clients.service import register_client, get_client, update_client, delete_client

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("/register", response_model=ClientResponse)
def register(
    client_data: ClientRegister,
    db: Session = Depends(get_db)
):
    """Register a new client - no JWT or email verification required"""
    return register_client(
        db,
        client_data.username,
        client_data.password,
        client_data.email,
        client_data.name
    )

@router.get("/{client_id}", response_model=ClientResponse)
def read_client(
    client_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Read client profile:
    - Client can always view their own profile
    - Barber can view client profile only if they have a confirmed/completed booking together
    - Requires require_active_client for clients (blocks deactivated accounts from viewing data)
    """
    user_type = user.get("user_type")
    
    # Apply require_active_client only for client users
    if user_type == "client":
        user = require_active_client(user, db)
    
    return get_client(db, client_id, user.get("user_id"), user_type)

@router.put("/{client_id}", response_model=ClientResponse)
def update_client_endpoint(
    client_id: int,
    client_data: ClientUpdate,
    verified_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    """
    Update client profile - client-only
    - Requires require_active_client AND require_verified_email
    - is_active field is NOT allowed (has dedicated delete flow)
    """
    verified_user = require_active_client(verified_user, db)
    return update_client(db, client_id, verified_user.get("user_id"), client_data.model_dump(exclude_unset=True))

@router.delete("/{client_id}")
def delete_client_endpoint(
    client_id: int,
    verified_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    """
    Deactivate client account - client-only self-service
    - Requires require_active_client AND require_verified_email
    - Cancels all future confirmed bookings using existing cancel_booking logic
    - Past/completed bookings remain as history
    """
    verified_user = require_active_client(verified_user, db)
    return delete_client(db, client_id, verified_user.get("user_id"))
