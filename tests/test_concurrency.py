"""
Concurrency tests for Booking creation and cancellation.
Tests use real Neon direct/unpooled connection, no mocking.
Uses pytest + httpx.AsyncClient + asyncio.gather for concurrent requests.
"""
import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
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
from app.base import Base
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
    """Helper to create a test user."""
    def _create_user(username, email, password, user_type, is_verified=True):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            user_type=user_type,
            is_verified=is_verified
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def test_client(db_session, test_user):
    """Create a test client with user."""
    def _create_client(username, email, password):
        user = test_user(username, email, password, "client")
        test_id = str(uuid.uuid4())[:8]
        client = Client(
            name=f"Client {username} {test_id}",
            user_id=user.id
        )
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)
        return client, user
    return _create_client


@pytest.fixture
def test_barber(db_session, test_user, test_shop):
    """Create a test barber with user."""
    def _create_barber(username, email, password, is_owner=False):
        user = test_user(username, email, password, "barber")
        test_id = str(uuid.uuid4())[:8]
        barber = Barber(
            name=f"Barber {username} {test_id}",
            shop_id=test_shop.id,
            is_owner=is_owner,
            slot_duration=30,
            user_id=user.id,
            is_active=True
        )
        db_session.add(barber)
        db_session.commit()
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
async def test_concurrent_booking_two_different_clients(
    db_session, test_shop, test_client, test_barber, 
    test_service, test_slot, client_jwt
):
    """
    Test: Two different clients try to book the same slot simultaneously.
    Expected: Exactly one succeeds (200), one fails (409), one booking exists, slot claimed.
    """
    test_id = str(uuid.uuid4())[:8]
    barber, _ = test_barber(f"barber{test_id}", f"barber{test_id}@test.com", "password123")
    slot = test_slot(barber)
    service = test_service
    
    # Link service to barber
    barber_service = BarberService(barber_id=barber.id, service_id=service.id)
    db_session.add(barber_service)
    db_session.commit()
    
    # Create two different clients
    client1, user1 = test_client(f"client1{test_id}", f"client1{test_id}@test.com", "password123")
    client2, user2 = test_client(f"client2{test_id}", f"client2{test_id}@test.com", "password123")
    
    # Get JWT tokens
    token1 = client_jwt(user1)
    token2 = client_jwt(user2)
    
    # Fire concurrent booking requests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        async def make_booking(token):
            response = await http_client.post(
                "/bookings",
                json={"slot_id": slot.id, "service_id": service.id},
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
        
        # Fire both requests simultaneously
        response1, response2 = await asyncio.gather(
            make_booking(token1),
            make_booking(token2)
        )
    
    # Assert response status codes
    status_codes = {response1.status_code, response2.status_code}
    assert status_codes == {200, 409}, f"Expected one 200 and one 409, got {status_codes}"
    
    # Determine which succeeded
    success_response = response1 if response1.status_code == 200 else response2
    fail_response = response2 if response1.status_code == 200 else response1
    
    # Verify success response contains booking
    success_data = success_response.json()
    assert "data" in success_data
    assert success_data["data"]["status"] == "confirmed"
    
    # Verify failure response contains error
    fail_data = fail_response.json()
    assert "error" in fail_data
    assert "message" in fail_data["error"]
    assert "already claimed" in fail_data["error"]["message"].lower()
    
    # Assert database state: exactly one booking exists
    # Use a fresh session to see committed changes from async requests
    fresh_session = SessionLocal()
    try:
        bookings = fresh_session.query(Booking).filter(Booking.slot_id == slot.id).all()
        assert len(bookings) == 1, f"Expected exactly 1 booking, found {len(bookings)}"
        
        booking = bookings[0]
        assert booking.status == "confirmed"
        assert booking.client_id in [client1.id, client2.id]
    finally:
        fresh_session.close()
    
    # Assert slot is claimed
    db_session.refresh(slot)
    assert slot.status == "claimed"


@pytest.mark.asyncio
async def test_concurrent_cancellation_same_client_double_tap(
    db_session, test_shop, test_client, test_barber, 
    test_service, test_slot, client_jwt
):
    """
    Test: Same client cancels the same booking twice simultaneously.
    Expected: Both succeed, booking cancelled once, slot open.
    """
    test_id = str(uuid.uuid4())[:8]
    barber, _ = test_barber(f"barber{test_id}", f"barber{test_id}@test.com", "password123")
    slot = test_slot(barber)
    service = test_service
    
    # Link service to barber
    barber_service = BarberService(barber_id=barber.id, service_id=service.id)
    db_session.add(barber_service)
    db_session.commit()
    
    # Create client and booking
    client, user = test_client(f"client{test_id}", f"client{test_id}@test.com", "password123")
    token = client_jwt(user)
    
    booking = Booking(
        slot_id=slot.id,
        client_id=client.id,
        barber_id=barber.id,
        shop_id=test_shop.id,
        service_id=service.id,
        status="confirmed"
    )
    db_session.add(booking)
    slot.status = "claimed"
    db_session.commit()
    db_session.refresh(booking)
    
    # Fire concurrent cancel requests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        async def cancel_booking():
            response = await http_client.patch(
                f"/bookings/{booking.id}/cancel",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
        
        response1, response2 = await asyncio.gather(
            cancel_booking(),
            cancel_booking()
        )
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Both should report cancelled status
    data1 = response1.json()
    data2 = response2.json()
    assert data1["data"]["booking_status"] == "cancelled_by_client"
    assert data2["data"]["booking_status"] == "cancelled_by_client"
    
    # Assert database state: exactly one booking, cancelled
    # Use a fresh session to see committed changes from async requests
    fresh_session = SessionLocal()
    try:
        bookings = fresh_session.query(Booking).filter(Booking.id == booking.id).all()
        assert len(bookings) == 1
    
        db_booking = bookings[0]
        assert db_booking.status == "cancelled_by_client"
    
    finally:
        fresh_session.close()
    
    # Assert slot is open
    db_session.refresh(slot)
    assert slot.status == "open"


@pytest.mark.asyncio
async def test_concurrent_cancellation_client_vs_barber(
    db_session, test_shop, test_client, test_barber, 
    test_service, test_slot, client_jwt
):
    """
    Test: Client and barber cancel the same booking simultaneously.
    Expected: Both succeed, booking cancelled by whoever won, slot open.
    """
    test_id = str(uuid.uuid4())[:8]
    barber, barber_user = test_barber(f"barber{test_id}", f"barber{test_id}@test.com", "password123")
    slot = test_slot(barber)
    service = test_service
    
    # Link service to barber
    barber_service = BarberService(barber_id=barber.id, service_id=service.id)
    db_session.add(barber_service)
    db_session.commit()
    
    # Create client and booking
    client, client_user = test_client(f"client{test_id}", f"client{test_id}@test.com", "password123")
    client_token = client_jwt(client_user)
    barber_token = client_jwt(barber_user)
    
    booking = Booking(
        slot_id=slot.id,
        client_id=client.id,
        barber_id=barber.id,
        shop_id=test_shop.id,
        service_id=service.id,
        status="confirmed"
    )
    db_session.add(booking)
    slot.status = "claimed"
    db_session.commit()
    db_session.refresh(booking)
    
    # Fire concurrent cancel requests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        async def cancel_as_client():
            response = await http_client.patch(
                f"/bookings/{booking.id}/cancel",
                headers={"Authorization": f"Bearer {client_token}"}
            )
            return response
        
        async def cancel_as_barber():
            response = await http_client.patch(
                f"/bookings/{booking.id}/cancel",
                headers={"Authorization": f"Bearer {barber_token}"}
            )
            return response
        
        client_response, barber_response = await asyncio.gather(
            cancel_as_client(),
            cancel_as_barber()
        )
    
    # Both should succeed
    assert client_response.status_code == 200
    assert barber_response.status_code == 200
    
    # Both should report a cancelled status (whichever won)
    client_data = client_response.json()
    barber_data = barber_response.json()
    
    client_status = client_data["data"]["booking_status"]
    barber_status = barber_data["data"]["booking_status"]
    
    # Both should be one of the cancelled states
    assert client_status in ["cancelled_by_client", "cancelled_by_barber"]
    assert barber_status in ["cancelled_by_client", "cancelled_by_barber"]
    
    # Assert database state: exactly one booking, in one cancelled state
    # Use a fresh session to see committed changes from async requests
    fresh_session = SessionLocal()
    try:
        bookings = fresh_session.query(Booking).filter(Booking.id == booking.id).all()
        assert len(bookings) == 1
        
        db_booking = bookings[0]
        assert db_booking.status in ["cancelled_by_client", "cancelled_by_barber"]
        
        # The losing request's response should reflect the actual final status
        assert client_status == db_booking.status or barber_status == db_booking.status
    finally:
        fresh_session.close()
    
    # Assert slot is open
    db_session.refresh(slot)
    assert slot.status == "open"


@pytest.mark.asyncio
async def test_concurrent_booking_same_client_double_tap(
    db_session, test_shop, test_client, test_barber, 
    test_service, test_slot, client_jwt
):
    """
    Test: Same client tries to book the same slot twice simultaneously.
    Expected: Both succeed (200) - idempotent behavior for same client.
    The second request should return the existing booking instead of 409.
    """
    test_id = str(uuid.uuid4())[:8]
    barber, _ = test_barber(f"barber{test_id}", f"barber{test_id}@test.com", "password123")
    slot = test_slot(barber)
    service = test_service
    
    # Link service to barber
    barber_service = BarberService(barber_id=barber.id, service_id=service.id)
    db_session.add(barber_service)
    db_session.commit()
    
    # Create single client
    client, user = test_client(f"client{test_id}", f"client{test_id}@test.com", "password123")
    token = client_jwt(user)
    
    # Fire concurrent booking requests from same client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        async def make_booking():
            response = await http_client.post(
                "/bookings",
                json={"slot_id": slot.id, "service_id": service.id},
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
        
        response1, response2 = await asyncio.gather(
            make_booking(),
            make_booking()
        )
    
    # Both should succeed (idempotent - same client's goal achieved)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Both should return booking details
    data1 = response1.json()
    data2 = response2.json()
    assert "data" in data1
    assert "data" in data2
    assert data1["data"]["status"] == "confirmed"
    assert data2["data"]["status"] == "confirmed"
    
    # Both should return the same booking (idempotent)
    assert data1["data"]["id"] == data2["data"]["id"]
    
    # Assert database state: exactly one booking exists
    # Use a fresh session to see committed changes from async requests
    fresh_session = SessionLocal()
    try:
        bookings = fresh_session.query(Booking).filter(Booking.slot_id == slot.id).all()
        assert len(bookings) == 1, f"Expected exactly 1 booking, found {len(bookings)}"
        
        booking = bookings[0]
        assert booking.status == "confirmed"
        assert booking.client_id == client.id
    finally:
        fresh_session.close()
    
    # Assert slot is claimed
    db_session.refresh(slot)
    assert slot.status == "claimed"
