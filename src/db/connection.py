from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import ssl
from src.config import settings

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    url = settings.DATABASE_URL,
    echo = True,
    connect_args = {"ssl": ssl_context}
)

async_session = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit = True
)

async def get_session():
    async with async_session() as session:
        yield session

