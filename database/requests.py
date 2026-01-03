from database.models import async_session, User
from sqlalchemy import select

async def add_user(data: dict, tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        
        if not user:
            session.add(User(
                telegram_id=tg_id,
                familiya=data['familiya'],
                ism=data['ism'],
                ota_ismi=data['ota_ismi'],
                jins=data['jins'],
                tugilgan_kun=data['tugilgan_kun'],
                telefon=data['telefon'],
                viloyat=data['viloyat'],
                tuman=data['tuman'],
                maktab=data['maktab'],
                sinf=data['sinf'],
                fan=data['fan'],
                til=data['til'],
                rasm_id=data['photo'],
                check_id=data['check'] # YANGI
            ))
            await session.commit()