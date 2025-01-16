import pytest
from sqlalchemy.exc import IntegrityError
from models.proxy import Proxy
from models.session import Session

def test_create_proxy(db_session):
    proxy = Proxy(
        ip="165.231.24.193",
        port=4444,
        username="andres",
        password="Andres2025"
    )
    db_session.add(proxy)
    db_session.commit()

    assert proxy.id is not None
    assert proxy.ip == "165.231.24.193"
    assert proxy.port == 4444
    assert proxy.username == "andres"
    assert proxy.password == "Andres2025"
    assert proxy.is_active is True

def test_proxy_session_relationship(db_session):
    proxy = Proxy(
        ip="165.231.24.193",
        port=4444,
        username="andres",
        password="Andres2025"
    )
    session = Session(
        username="iguser",
        password="igpass",
        proxy=proxy
    )
    db_session.add_all([proxy, session])
    db_session.commit()

    assert len(proxy.sessions) == 1
    assert proxy.sessions[0] == session
    assert session.proxy == proxy

def test_proxy_required_fields(db_session):
    proxy = Proxy()
    db_session.add(proxy)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_proxy_string_representation(db_session):
    proxy = Proxy(
        ip="165.231.24.193",
        port=4444,
        username="andres",
        password="Andres2025"
    )
    assert str(proxy) == "165.231.24.193:4444:andres:Andres2025"
