import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
async def client():
    """Cliente HTTP que llama a la app de FastAPI directamente en memoria,
    sin arrancar un servidor real (ASGITransport habla el protocolo ASGI
    de la app en vez de hacer una petición de red de verdad).

    Antes de cada test se recrean las tablas desde cero, para que un test
    nunca vea datos dejados por el anterior.
    """
    # Cada test de pytest-asyncio corre en su propio bucle de eventos nuevo;
    # el "engine" se creó una sola vez al importar app.database, con
    # conexiones ligadas al bucle del primer test. dispose() las cierra, así
    # las siguientes que se abran quedan ligadas al bucle del test actual.
    await engine.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
