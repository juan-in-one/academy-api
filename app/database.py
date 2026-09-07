from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Crea las tablas si no existen. Uso solo para desarrollo local;
    en el clúster esto se gestionará con Alembic (paso futuro del roadmap)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
