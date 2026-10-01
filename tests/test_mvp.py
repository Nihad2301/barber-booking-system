"""
MVP-scope test suite - 6 critical-path tests.
Tests use real Neon direct/unpooled connection, no mocking.
Uses pytest + httpx.AsyncClient for HTTP requests.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.auth.security import hash_password, generate_token
from app.auth.models import User
from app.shops.models import Shop
from app.barbers.models import Barber, BarberService
from app.clients.models import Client
from app.services.models import Service
from app.slots.models import Slot
from app.bookings.models import Booking
from app.working_hours.models import WorkingHours
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use direct/unpooled connection for tests
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data(db_session):
    """Cleanup test data before and after each test."""
    # Cleanup before test
    db_session.query(Booking).delete()
    db_session.query(Slot).delete()
    db_session.query(BarberService).delete()
    db_session.query(Service).delete()
    db_session.query(Client).delete()
    db_session.query(WorkingHours).delete()
    db_session.query(Barber).delete()
    db_session.query(Shop).delete()
    db_session.query(User).delete()
    db_session.commit()
    
    yield
    
    # Cleanup after test
    db_session.query(Booking).delete()
    db_session.query(Slot).delete()
    db_session.query(BarberService).delete()
    db_session.query(Service).delete()
    db_session.query(Client).delete()
    db_session.query(WorkingHours).delete()
    db_session.query(Barber).delete()
    db_session.query(Shop).delete()
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture
def test_shop(db_session):
    """Create a test shop."""
    test_id = str(uuid.uuid4())[:8]
    shop = Shop(
        name=f"Test Shop {test_id}",
        location="Test Location",
        accepting_new_barbers=True,
        is_active=True
    )
    db_session.add(shop)
    db_session.commit()
    db_session.refresh(shop)
    return shop


@pytest.fixture
def test_user(db_session):
    """Helper to create a test user (does not commit - caller handles transaction)."""
    def _create_user(username, email, password, user_type, is_verified=True):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            user_type=user_type,
            is_verified=is_verified
        )
        db_session.add(user)
        db_session.flush()  # Get ID without committing
        return user
    return _create_user


@pytest.fixture
def test_client(db_session, test_user):
    """Create a test client with user (single transaction)."""
    def _create_client(username, email, password, is_active=True):
        user = test_user(username, email, password, "client")
        test_id = str(uuid.uuid4())[:8]
        client = Client(
            name=f"Client {username} {test_id}",
            user_id=user.id,
            is_active=is_active
        )
        db_session.add(client)
        db_session.commit()  # Single commit for user + client
        db_session.refresh(client)
        return client, user
    return _create_client


@pytest.fixture
def test_barber(db_session, test_user, test_shop):
    """Create a test barber with user (single transaction)."""
    def _create_barber(username, email, password, is_owner=False, is_active=True):
        user = test_user(username, email, password, "barber")
        test_id = str(uuid.uuid4())[:8]
        barber = Barber(
            name=f"Barber {username} {test_id}",
            shop_id=test_shop.id,
            is_owner=is_owner,
            slot_duration=30,
            user_id=user.id,
            is_active=is_active
        )
        db_session.add(barber)
        db_session.commit()  # Single commit for user + barber
        db_session.refresh(barber)
        return barber, user
    return _create_barber


@pytest.fixture
def test_service(db_session, test_shop):
    """Create a test service."""
    test_id = str(uuid.uuid4())[:8]
    service = Service(
        name=f"Haircut {test_id}",
        price=25.00,
        shop_id=test_shop.id,
        is_active=True
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def test_slot(db_session, test_shop):
    """Create a test open slot - requires barber to be passed."""
    def _create_slot(barber):
        slot = Slot(
            barber_id=barber.id,
            shop_id=test_shop.id,
            start_time=datetime.utcnow() + timedelta(days=1, hours=10),
            end_time=datetime.utcnow() + timedelta(days=1, hours=10, minutes=30),
            status="open"
        )
        db_session.add(slot)
        db_session.commit()
        db_session.refresh(slot)
        return slot
    return _create_slot


@pytest.fixture
def client_jwt():
    """Helper to generate JWT token for a user."""
    def _get_token(user):
        return generate_token(data={"user_id": user.id, "user_type": user.user_type})
    return _get_token


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(db_session, test_client):
    """
    Test: Attempt login with valid username and incorrect password.
    Expected: Request rejected with 401, no token issued.
    """
    client, user = test_client("testuser", "test@example.com", "correctpassword")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        response = await http_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
    
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_invalid_jwt(db_session, test_client):
    """
    Test: Call protected endpoint with missing JWT and with malformed JWT.
    Expected: Both rejected (403 for missing, 401 for malformed), endpoint logic never executes.
    """
    client, user = test_client("testuser", "test@example.com", "password123")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        # Test with missing JWT (FastAPI HTTPBearer returns 403)
        response_no_token = await http_client.get("/bookings")
        assert response_no_token.status_code == 403
        
        # Test with malformed JWT (returns 401 from verify_token)
        response_bad_token = await http_client.get(
            "/bookings",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert response_bad_token.status_code == 401


@pytest.mark.asyncio
async def test_client_cannot_read_other_client(db_session, test_client, client_jwt):
    """
    Test: Client A attempts to read Client B's profile via GET /clients/{B's id}.
    Expected: 403 Forbidden.
    """
    client_a, user_a = test_client("clienta", "clienta@example.com", "password123")
    client_b, user_b = test_client("clientb", "clientb@example.com", "password123")
    token_a = client_jwt(user_a)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        response = await http_client.get(
            f"/clients/{client_b.id}",
            headers={"Authorization": f"Bearer {token_a}"}
        )
    
    assert response.status_code == 403
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_barber_cannot_act_on_other_shops_resource(db_session, test_shop, test_barber, test_service, client_jwt):
    """
    Test: Barber from Shop A attempts to update a service belonging to Shop B.
    Expected: 403 Forbidden.
    """
    # Create barber in Shop A
    barber_a, user_a = test_barber("barber_a", "barber_a@example.com", "password123", is_owner=True)
    token_a = client_jwt(user_a)
    
    # Create a second shop
    test_id = str(uuid.uuid4())[:8]
    shop_b = Shop(
        name=f"Shop B {test_id}",
        location="Location B",
        accepting_new_barbers=True,
        is_active=True
    )
    db_session.add(shop_b)
    db_session.commit()
    db_session.refresh(shop_b)
    
    # Create a service in Shop B
    service_b = Service(
        name="Service B",
        price=30.00,
        shop_id=shop_b.id,
        is_active=True
    )
    db_session.add(service_b)
    db_session.commit()
    db_session.refresh(service_b)
    
    # Barber A attempts to update Shop B's service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        response = await http_client.put(
            f"/services/{shop_b.id}/{service_b.id}",
            json={"name": "Hacked Service", "price": 999.00},
            headers={"Authorization": f"Bearer {token_a}"}
        )
    
    assert response.status_code == 403
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_deactivated_account_blocked_from_protected_endpoint(db_session, test_client, client_jwt):
    """
    Test: Deactivate a client account, then attempt to call protected endpoint with still-valid JWT.
    Expected: 403, blocked via require_active_client.
    """
    # Create client with is_active=False
    client, user = test_client("testuser", "test@example.com", "password123", is_active=False)
    token = client_jwt(user)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        response = await http_client.get(
            "/bookings",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 403
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_client_cannot_cancel_other_clients_booking(db_session, test_shop, test_client, test_barber, test_service, test_slot, client_jwt):
    """
    Test: Client A has a confirmed booking. Client B attempts to cancel Client A's booking.
    Expected: 403 Forbidden, booking remains 'confirmed'.
    """
    test_id = str(uuid.uuid4())[:8]
    barber, _ = test_barber(f"barber{test_id}", f"barber{test_id}@test.com", "password123")
    slot = test_slot(barber)
    service = test_service
    
    # Link service to barber
    barber_service = BarberService(barber_id=barber.id, service_id=service.id)
    db_session.add(barber_service)
    db_session.commit()
    
    # Create two clients
    client_a, user_a = test_client(f"clienta{test_id}", f"clienta{test_id}@test.com", "password123")
    client_b, user_b = test_client(f"clientb{test_id}", f"clientb{test_id}@test.com", "password123")
    
    token_a = client_jwt(user_a)
    token_b = client_jwt(user_b)
    
    # Create booking for Client A
    booking = Booking(
        slot_id=slot.id,
        client_id=client_a.id,
        barber_id=barber.id,
        shop_id=test_shop.id,
        service_id=service.id,
        status="confirmed"
    )
    db_session.add(booking)
    slot.status = "claimed"
    db_session.commit()
    db_session.refresh(booking)
    
    # Client B attempts to cancel Client A's booking
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        response = await http_client.patch(
            f"/bookings/{booking.id}/cancel",
            headers={"Authorization": f"Bearer {token_b}"}
        )
    
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    
    # Verify booking remains confirmed
    db_session.refresh(booking)
    assert booking.status == "confirmed"
