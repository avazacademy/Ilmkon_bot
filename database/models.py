from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# Baza fayli
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    familiya: Mapped[str] = mapped_column(String(50))
    ism: Mapped[str] = mapped_column(String(50))
    ota_ismi: Mapped[str] = mapped_column(String(50))
    jins: Mapped[str] = mapped_column(String(20))
    tugilgan_kun: Mapped[str] = mapped_column(String(20))
    telefon: Mapped[str] = mapped_column(String(20))
    viloyat: Mapped[str] = mapped_column(String(50))
    tuman: Mapped[str] = mapped_column(String(50))
    maktab: Mapped[str] = mapped_column(String(100))
    sinf: Mapped[str] = mapped_column(String(20))
    fan: Mapped[str] = mapped_column(String(50))
    til: Mapped[str] = mapped_column(String(20))
    rasm_id: Mapped[str] = mapped_column(String(255))
    check_id: Mapped[str] = mapped_column(String(255)) # YANGI: Chek IDsi

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)