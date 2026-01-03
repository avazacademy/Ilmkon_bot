import os
import csv
import time
import tempfile
import asyncio
from typing import List, Optional
from aiogram.types import FSInputFile, ReplyKeyboardRemove

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from sqlalchemy import select, delete, update

from database.models import async_session, User
from config import ADMIN_LIST
from keyboards.reply import admin_panel
from states.register_state import AdminState

router = Router()

# ---------- SOZLAMALAR ----------
PAGE_SIZE = 10  # sahifalash: har sahifada nechta user ko'rsatiladi


# ---------- ADMIN LIST NI NORMALIZATSIYA QILISH ----------
def _normalize_admin_list(admins) -> List[int]:
    if not admins:
        return []
    if isinstance(admins, int):
        return [admins]
    if isinstance(admins, (list, tuple)):
        out = []
        for x in admins:
            try:
                out.append(int(x))
            except Exception:
                continue
        return out
    if isinstance(admins, str):
        parts = [p.strip() for p in admins.split(",") if p.strip()]
        out = []
        for p in parts:
            try:
                out.append(int(p))
            except Exception:
                continue
        return out
    return []


NORMALIZED_ADMINS = _normalize_admin_list(ADMIN_LIST)


def is_admin(user_id: int) -> bool:
    return user_id in NORMALIZED_ADMINS


# ---------- YORDAMCHI: USERLARNI OQISH ----------
async def _fetch_all_users() -> List[User]:
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    return users


# ---------- ADMIN PANELGA KIRISH ----------
@router.message(Command("admin"))
async def admin_login(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "👨‍💻 <b>Admin panelga xush kelibsiz!</b>\nKerakli bo'limni tanlang:",
            reply_markup=admin_panel,
            parse_mode="HTML",
        )
    else:
        await message.answer("Sizda admin huquqlari yo'q.")


# ---------- STATISTIKA: sahifa va har bir user uchun tugmalar ----------
def _make_stats_keyboard(users_page: List[User], page: int, total: int) -> InlineKeyboardMarkup:
    kb_rows = []
    # Har user uchun alohida satr: ℹ️ va 🗑️ tugmalari (callbacklarda user.id bor)
    for user in users_page:
        fam = getattr(user, "familiya", "") or ""
        ism = getattr(user, "ism", "") or ""
        label = f"{fam} {ism}".strip() or f"#{getattr(user,'id', '')}"
        # Qo'shimcha: agar to'lov chekini tekshirish kerak bo'lsa, admin tomonidan tekshirish tugmasi yaratish mumkin:
        # InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"check_confirm_{user.id}")
        # InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"check_reject_{user.id}")
        kb_rows.append(
            [
                InlineKeyboardButton(text=f"ℹ️ {label}", callback_data=f"view_{user.id}"),
                InlineKeyboardButton(text=f"🗑️ O'chirish", callback_data=f"del_{user.id}"),
            ]
        )

    # Sahifalash tugmalari
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE if total else 1
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"stats_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"Sahifa {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"stats_page_{page+1}"))
    kb_rows.append(nav_row)

    # Export va refresh tugmalari
    kb_rows.append(
        [
            InlineKeyboardButton(text="📥 Eksport CSV", callback_data="stats_export_csv"),
            InlineKeyboardButton(text="📤 Eksport XLSX", callback_data="stats_export_xlsx"),
            InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"stats_page_{page}"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


@router.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    # yuborishda botni ishlatamiz
    await _send_stats_page(message.bot, chat_id=message.chat.id, page=1)


async def _send_stats_page(bot: Bot, chat_id: int, page: int = 1, edit_message: Optional[types.Message] = None):
    users_all = await _fetch_all_users()
    total = len(users_all)
    if total == 0:
        await bot.send_message(chat_id=chat_id, text="📂 Baza hozircha bo'sh.")
        return

    offset = (page - 1) * PAGE_SIZE
    users_page = users_all[offset : offset + PAGE_SIZE]

    text = f"📊 <b>Jami a'zolar: {total} ta</b>\n\n"
    for i, user in enumerate(users_page, start=offset + 1):
        fam = getattr(user, "familiya", "") or ""
        ism = getattr(user, "ism", "") or ""
        sinf = getattr(user, "sinf", "") or ""
        tel = getattr(user, "telefon", "") or ""
        text += f"{i}. {fam} {ism} ({sinf}-sinf) - {tel}\n"

    kb = _make_stats_keyboard(users_page, page, total)

    if edit_message:
        try:
            await edit_message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            return
        except Exception:
            pass

    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)


# ---------- CALLBACK: sahifalash ----------
@router.callback_query(F.data.startswith("stats_page_"))
async def stats_page_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    try:
        page = int(callback.data.split("_")[-1])
    except Exception:
        page = 1
    # edit qilishni sinab ko'ramiz, agar bo'lmasa yangi yuboramiz
    await _send_stats_page(callback.message.bot, chat_id=callback.message.chat.id, page=page, edit_message=callback.message)
    await callback.answer()

@router.message(F.text == "📢 Reklama yuborish")
async def ask_ad_content(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_LIST:
        await message.answer(
            "📢 <b>Reklama yuborish rejimi.</b>\n\n"
            "Foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
            "<i>(Matn, Rasm, Video yoki Ovozli xabar bo'lishi mumkin)</i>\n\n"
            "❌ Bekor qilish uchun /cancel deb yozing.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove() # Chalg'itmasligi uchun tugmalarni olib turamiz
        )
        # Botni "Kutish" rejimiga o'tkazamiz
        await state.set_state(AdminState.waiting_for_ad)

# ==========================================
# 🚀 3. REKLAMANI TARQATISH (Eng muhim qism)
# ==========================================
@router.message(AdminState.waiting_for_ad)
async def send_ad_to_users(message: types.Message, state: FSMContext, bot: Bot):
    # Bekor qilish
    if message.text == "/cancel":
        await message.answer("❌ Reklama yuborish bekor qilindi.", reply_markup=admin_panel)
        await state.clear()
        return

    status_msg = await message.answer("⏳ <b>Xabar yuborish boshlandi...</b>", parse_mode="HTML")
    
    sent = 0
    blocked = 0
    
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
    for user in users:
        try:
            # copy_message - har qanday xabarni (rasm, video, tekst) nusxalaydi
            await bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            sent += 1
            await asyncio.sleep(0.05) # Spam bo'lmasligi uchun pauza
        except Exception:
            blocked += 1 # Botni bloklaganlar
            
    await status_msg.delete()
    
    await message.answer(
        f"✅ <b>Reklama yakunlandi!</b>\n\n"
        f"📤 Yuborildi: {sent} ta\n"
        f"🚫 Yetib bormadi (blok): {blocked} ta",
        reply_markup=admin_panel,
        parse_mode="HTML"
    )
    # Holatdan chiqamiz
    await state.clear()


# ==========================================
# 🔙 5. CHIQISH
# ==========================================
@router.message(F.text == "🔙 Chiqish")
async def admin_logout(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_LIST:
        await state.clear()
        await message.answer("Admin panel yopildi.", reply_markup=types.ReplyKeyboardRemove())
        
        
# ---------- CALLBACK: view user ----------
@router.callback_query(F.data.startswith("view_"))
async def view_user_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    try:
        user_id = int(callback.data.split("_", 1)[1])
    except Exception:
        await callback.answer("Noto'g'ri ma'lumot", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Foydalanuvchi topilmadi yoki o'chirilgan.", show_alert=True)
        return

    # Batafsil ma'lumotni yuboramiz
    fam = getattr(user, "familiya", "") or ""
    ism = getattr(user, "ism", "") or ""
    ota = getattr(user, "ota_ismi", "") or ""
    tel = getattr(user, "telefon", "") or ""
    vil = getattr(user, "viloyat", "") or ""
    tum = getattr(user, "tuman", "") or ""
    mak = getattr(user, "maktab", "") or ""
    sinf = getattr(user, "sinf", "") or ""
    fan = getattr(user, "fan", "") or ""
    til = getattr(user, "til", "") or ""
    tg_id = getattr(user, "telegram_id", "") or ""
    suk = getattr(user, "tugilgan_kun", "") or ""

    info = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"<b>Ism:</b> {ism}\n"
        f"<b>Familiya:</b> {fam}\n"
        f"<b>Ota:</b> {ota}\n"
        f"<b>Telefon:</b> {tel}\n"
        f"<b>Telegram ID:</b> {tg_id}\n"
        f"<b>Viloyat:</b> {vil}\n"
        f"<b>Tuman:</b> {tum}\n"
        f"<b>Maktab:</b> {mak}\n"
        f"<b>Sinf:</b> {sinf}\n"
        f"<b>Fan:</b> {fan}\n"
        f"<b>Til:</b> {til}\n"
        f"<b>Tug'ilgan sana:</b> {suk}\n"
    )

    # Qayta tasdiqlash va o'chirish tugmalari
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"check_confirm_{user.id}"),
            InlineKeyboardButton(text="❌ To'lovni bekor qilish", callback_data=f"check_reject_{user.id}"),
        ],
        [
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"del_{user.id}"),
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="stats_page_1"),
        ]
    ])
    await callback.message.reply(text=info, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ---------- CALLBACK: delete (bosilganda tasdiq so'raydi) ----------
@router.callback_query(F.data.startswith("del_"))
async def del_user_request(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    try:
        user_id = int(callback.data.split("_", 1)[1])
    except Exception:
        await callback.answer("Noto'g'ri ma'lumot", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"delconf_{user_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="stats_page_1"),
        ]
    ])
    await callback.message.answer(f"⚠️ Siz ushbu foydalanuvchini o'chirmoqchimisiz? ID: {user_id}", reply_markup=kb)
    await callback.answer()


# ---------- CALLBACK: delete confirmed ----------
@router.callback_query(F.data.startswith("delconf_"))
async def del_user_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    try:
        user_id = int(callback.data.split("_", 1)[1])
    except Exception:
        await callback.answer("Noto'g'ri ma'lumot", show_alert=True)
        return

    async with async_session() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()

    await callback.message.answer(f"✅ ID:{user_id} bo'lgan foydalanuvchi bazadan o'chirildi.")
    # Sahifani yangilash: 1-sahifani yuborish
    await _send_stats_page(callback.message.bot, chat_id=callback.message.chat.id, page=1)
    await callback.answer("O'chirildi.")


# ---------- PAYMENT: helper to update DB user payment status ----------
async def _set_user_payment_flag(user_id: int, confirmed: bool) -> bool:
    """
    Urinib ko'radi va agar User modelida keng tarqalgan to'lov maydonlari bo'lsa,
    ularni yangilaydi. Agar hech qanday maydon topilmasa, faqat True/False qaytaradi
    bo'ladi (operation success).
    """
    common_fields_true = ["paid", "is_paid", "payment_confirmed"]
    common_fields_status = ["payment_status", "status"]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        updated = False
        # birinchi turdagi boolean maydonlarni yangilashga urinib ko'ramiz
        for field in common_fields_true:
            if hasattr(user, field):
                try:
                    setattr(user, field, True if confirmed else False)
                    updated = True
                except Exception:
                    continue

        # keyingi turdagi maydonlarga 'confirmed'/'rejected' kabi qiymat beramiz
        for field in common_fields_status:
            if hasattr(user, field):
                try:
                    setattr(user, field, "confirmed" if confirmed else "rejected")
                    updated = True
                except Exception:
                    continue

        # Agar hech narsa yangilanmagan bo'lsa — lekin user mavjud bo'lsa success True qaytaramiz
        if updated:
            try:
                await session.commit()
            except Exception:
                try:
                    await session.rollback()
                except Exception:
                    pass
                return False
        return True


# ---------- PAYMENT: Tasdiqlash va Bekor qilish CALLBACKLARI ----------
# ... (boshqa importlar)
from sqlalchemy import select, update

# ✅ TO'LOVNI TASDIQLASH
@router.callback_query(F.data.startswith("check_confirm_"))
async def payment_confirm_callback(callback: CallbackQuery, bot: Bot):
    # Admin tekshiruvi
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    # 1. Telegram ID ni tugmadan olamiz
    try:
        user_telegram_id = int(callback.data.split("_", 2)[2])
    except Exception:
        await callback.answer("Xatolik: ID topilmadi", show_alert=True)
        return

    admin_name = callback.from_user.full_name or "Admin"
    original_caption = callback.message.caption or ""

    # 2. Foydalanuvchiga DARHOL xabar yuboramiz (Bazani kutib o'tirmaymiz)
    sent_ok = False
    try:
        await bot.send_message(
            chat_id=user_telegram_id,
            text="✅ <b>Tabriklaymiz! To'lovingiz tasdiqlandi.</b>\n\nSiz \"ZUKKO MATEMATIK-2026\" tanlovining rasmiy ishtirokchisiga aylandingiz!",
            parse_mode="HTML"
        )
        sent_ok = True
    except Exception as e:
        print(f"❌ Xabar yuborishda xato: {e}")

    # 3. Bazada to'lovni tasdiqlaymiz (telegram_id bo'yicha qidiramiz)
    try:
        async with async_session() as session:
            # Userni telegram_id orqali topamiz
            result = await session.execute(select(User).where(User.telegram_id == user_telegram_id))
            user = result.scalar_one_or_none()
            
            if user:
                # Kerakli ustunlarni True qilamiz (Modelizga qarab)
                if hasattr(user, "paid"): user.paid = True
                if hasattr(user, "is_paid"): user.is_paid = True
                if hasattr(user, "payment_confirmed"): user.payment_confirmed = True
                if hasattr(user, "status"): user.status = "confirmed"
                await session.commit()
            else:
                print(f"⚠️ Bazada user topilmadi: {user_telegram_id}")
    except Exception as e:
        print(f"⚠️ Bazani yangilashda xato: {e}")

    # 4. Guruhdagi xabarni o'zgartirish
    new_caption = original_caption + f"\n\n✅ <b>QABUL QILINDI</b>\nTasdiqladi: {admin_name}"
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except:
        try:
            await callback.message.edit_text(new_caption, parse_mode="HTML", reply_markup=None)
        except: pass

    # 5. Admin javobi
    if sent_ok:
        await callback.answer("Tasdiqlandi va userga xabar yuborildi!", show_alert=False)
    else:
        await callback.answer("Tasdiqlandi, lekin userga xabar bormadi (Bloklagan bo'lishi mumkin).", show_alert=True)


# ❌ TO'LOVNI BEKOR QILISH
@router.callback_query(F.data.startswith("check_reject_"))
async def payment_reject_callback(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    try:
        user_telegram_id = int(callback.data.split("_", 2)[2])
    except Exception:
        await callback.answer("Xatolik: ID topilmadi", show_alert=True)
        return

    admin_name = callback.from_user.full_name or "Admin"
    original_caption = callback.message.caption or ""

    # 1. Userga xabar yuborish
    sent_ok = False
    try:
        await bot.send_message(
            chat_id=user_telegram_id,
            text="❌ <b>To'lovingiz bekor qilindi.</b>\n\nChekda xatolik bor yoki to'lov tushmagan. Iltimos, tekshirib qayta yuboring yoki admin bilan bog'laning.",
            parse_mode="HTML"
        )
        sent_ok = True
    except Exception as e:
        print(f"❌ Xabar yuborishda xato: {e}")

    # 2. Bazada bekor qilish (telegram_id bo'yicha)
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_telegram_id))
            user = result.scalar_one_or_none()
            
            if user:
                if hasattr(user, "paid"): user.paid = False
                if hasattr(user, "status"): user.status = "rejected"
                await session.commit()
    except Exception:
        pass

    # 3. Guruhdagi xabarni yangilash
    new_caption = original_caption + f"\n\n❌ <b>BEKOR QILINDI</b>\nRad etdi: {admin_name}"
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except:
        try:
            await callback.message.edit_text(new_caption, parse_mode="HTML", reply_markup=None)
        except: pass

    if sent_ok:
        await callback.answer("Bekor qilindi va xabar yuborildi.", show_alert=False)
    else:
        await callback.answer("Bekor qilindi, lekin userga xabar bormadi.", show_alert=True)

# ---------- CSV va XLSX eksport ----------
async def _make_csv_file(users: List[User]) -> str:
    with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8-sig", suffix=".csv") as tmp:
        writer = csv.writer(tmp, delimiter=";")
        writer.writerow(["ID", "Telegram ID", "Familiya", "Ism", "Ota ismi", "Telefon", "Viloyat", "Tuman", "Maktab", "Sinf", "Fan", "Til", "Sana"])
        for user in users:
            writer.writerow([
                getattr(user, "id", ""),
                getattr(user, "telegram_id", ""),
                getattr(user, "familiya", "") or "",
                getattr(user, "ism", "") or "",
                getattr(user, "ota_ismi", "") or "",
                getattr(user, "telefon", "") or "",
                getattr(user, "viloyat", "") or "",
                getattr(user, "tuman", "") or "",
                getattr(user, "maktab", "") or "",
                getattr(user, "sinf", "") or "",
                getattr(user, "fan", "") or "",
                getattr(user, "til", "") or "",
                getattr(user, "tugilgan_kun", "") or ""
            ])
        return tmp.name


async def _make_xlsx_file(users: List[User]) -> str:
    try:
        from openpyxl import Workbook
    except ImportError:
        raise RuntimeError("openpyxl o'rnatilmagan. pip install openpyxl")

    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "Telegram ID", "Familiya", "Ism", "Ota ismi", "Telefon", "Viloyat", "Tuman", "Maktab", "Sinf", "Fan", "Til", "Sana"])
    for user in users:
        ws.append([
            getattr(user, "id", ""),
            getattr(user, "telegram_id", ""),
            getattr(user, "familiya", "") or "",
            getattr(user, "ism", "") or "",
            getattr(user, "ota_ismi", "") or "",
            getattr(user, "telefon", "") or "",
            getattr(user, "viloyat", "") or "",
            getattr(user, "tuman", "") or "",
            getattr(user, "maktab", "") or "",
            getattr(user, "sinf", "") or "",
            getattr(user, "fan", "") or "",
            getattr(user, "til", "") or "",
            getattr(user, "tugilgan_kun", "") or ""
        ])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    wb.save(tmp.name)
    return tmp.name


@router.callback_query(F.data == "stats_export_csv")
async def export_csv_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    wait = await callback.message.answer("⏳ CSV fayl yaratilmoqda...")
    users = await _fetch_all_users()
    if not users:
        await wait.edit_text("📂 Bazada ma'lumot yo'q.")
        await asyncio.sleep(1.5)
        await wait.delete()
        return

    path = None
    try:
        path = await _make_csv_file(users)
        await callback.message.answer_document(document=FSInputFile(path), caption=f"📂 Jami: {len(users)} ta")
    except Exception as e:
        await callback.message.answer(f"❌ CSV yaratishda xato: {e}")
    finally:
        try:
            await wait.delete()
        except Exception:
            pass
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    await callback.answer()


@router.callback_query(F.data == "stats_export_xlsx")
async def export_xlsx_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    wait = await callback.message.answer("⏳ XLSX fayl yaratilmoqda...")
    users = await _fetch_all_users()
    if not users:
        await wait.edit_text("📂 Bazada ma'lumot yo'q.")
        await asyncio.sleep(1.5)
        await wait.delete()
        return

    path = None
    try:
        path = await _make_xlsx_file(users)
        await callback.message.answer_document(document=FSInputFile(path), caption=f"📂 Jami: {len(users)} ta")
    except Exception as e:
        await callback.message.answer(f"❌ XLSX yaratishda xato: {e}")
    finally:
        try:
            await wait.delete()
        except Exception:
            pass
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    await callback.answer()