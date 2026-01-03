import re
from datetime import datetime
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from states.register_state import RegisterState
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import reply, inline
from config import GROUP_ID
from database.requests import add_user

router = Router()

# ==========================================
# 🛠 1. YORDAMCHI FUNKSIYALAR (VALIDATSIYA)
# ==========================================

def validate_date(date_text):
    """Sanani KK.OO.YYYY formatida ekanligini tekshiradi"""
    try:
        datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def validate_phone(phone_text):
    """Telefon raqam formatini tekshiradi (+998xxxxxxxxx)"""
    # Ortiqcha belgilarni tozalash
    phone_text = phone_text.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Formatlash
    if not phone_text.startswith("+"):
        if phone_text.startswith("998"):
            phone_text = "+" + phone_text
        elif len(phone_text) == 9:
            phone_text = "+998" + phone_text
            
    # Regex tekshiruvi
    match = re.match(r"^\+998\d{9}$", phone_text)
    return match.group() if match else None

# ==========================================
# 🚀 2. ASOSIY JARAYON (HANDLERLAR)
# ==========================================

# 1. Familiya
@router.message(RegisterState.familiya)
async def process_familiya(message: types.Message, state: FSMContext):
    await state.update_data(familiya=message.text)
    await message.answer("<b>Ismingizni</b> kiriting:", parse_mode="HTML")
    await state.set_state(RegisterState.ism)

# 2. Ism
@router.message(RegisterState.ism)
async def process_ism(message: types.Message, state: FSMContext):
    await state.update_data(ism=message.text)
    await message.answer("<b>Otangizning ismini</b> kiriting:", parse_mode="HTML")
    await state.set_state(RegisterState.ota_ismi)

# 3. Ota ismi
@router.message(RegisterState.ota_ismi)
async def process_ota(message: types.Message, state: FSMContext):
    await state.update_data(ota_ismi=message.text)
    await message.answer("Jinsingizni tanlang:", reply_markup=inline.jins_kb)
    await state.set_state(RegisterState.jins)

# 4. Jins
@router.callback_query(RegisterState.jins)
async def process_jins(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(jins=callback.data)
    await callback.message.delete()
    await callback.message.answer(
        "Tug'ilgan kuningizni quyidagi formatda yozing:\n"
        "<b>KK.OO.YYYY</b>\n\n"
        "<i>Masalan: 15.04.2005</i>", 
        parse_mode="HTML"
    )
    await state.set_state(RegisterState.tugilgan_kun)

# 5. Tug'ilgan kun
@router.message(RegisterState.tugilgan_kun)
async def process_bd(message: types.Message, state: FSMContext):
    date_text = message.text.strip()
    if not validate_date(date_text):
        await message.answer(
            "⚠️ <b>Xato format!</b>\nIltimos, sanani faqat raqamlar bilan yozing: <b>15.04.2005</b>",
            parse_mode="HTML"
        )
        return

    await state.update_data(tugilgan_kun=date_text)
    await message.answer(
        "Telefon raqamingizni kiriting.\n"
        "Pastdagi tugmani bosing yoki qo'lda yozing (+998...):",
        reply_markup=reply.phone_kb
    )
    await state.set_state(RegisterState.telefon)

# 6. Telefon
@router.message(RegisterState.telefon)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
        if not phone_number.startswith("+"): phone_number = "+" + phone_number
    elif message.text:
        phone_number = validate_phone(message.text)
        
    if not phone_number:
        await message.answer("⚠️ <b>Noto'g'ri raqam!</b>\nIltimos, O'zbekiston raqamini kiriting.", parse_mode="HTML")
        return

    await state.update_data(telefon=phone_number)
    await message.answer("Viloyatni tasdiqlang:", reply_markup=inline.viloyat_kb)
    await state.set_state(RegisterState.viloyat)

# 7. Viloyat
@router.callback_query(RegisterState.viloyat)
async def process_region(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(viloyat=callback.data)
    await callback.message.delete()
    await callback.message.answer("Tumaningizni tanlang:", reply_markup=inline.tuman_kb)
    await state.set_state(RegisterState.tuman)

# 8. Tuman
@router.callback_query(RegisterState.tuman)
async def process_dist(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tuman=callback.data)
    await callback.message.delete()
    await callback.message.answer("Maktabingiz raqamini yoki nomini yozing: <i>Masalan: 22-maktab</i>", parse_mode="HTML")
    await state.set_state(RegisterState.maktab)

# 9. Maktab
@router.message(RegisterState.maktab)
async def process_school(message: types.Message, state: FSMContext):
    await state.update_data(maktab=message.text)
    await message.answer("Sinfingizni tanlang:", reply_markup=inline.sinf_kb)
    await state.set_state(RegisterState.sinf)

# 10. Sinf
@router.callback_query(RegisterState.sinf)
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(sinf=callback.data)
    await callback.message.delete()
    await callback.message.answer("Qaysi fandan qatnashasiz? (Fanni yozib yuboring):")
    await state.set_state(RegisterState.fan)

# 11. Fan
@router.message(RegisterState.fan)
async def process_subject(message: types.Message, state: FSMContext):
    await state.update_data(fan=message.text)
    await message.answer("Ta'lim tilini tanlang:", reply_markup=inline.lang_kb)
    await state.set_state(RegisterState.til)

# 12. Til
@router.callback_query(RegisterState.til)
async def process_lang(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(til=callback.data)
    await callback.message.delete()
    await callback.message.answer("📸 Iltimos, <b>o'zingizning sifatli rasmingizni</b> yuboring:", parse_mode="HTML")
    await state.set_state(RegisterState.photo)

# 13. Rasm -> TASDIQLASH
@router.message(RegisterState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    
    data = await state.get_data()
    
    caption = (
        f"<b>📋 Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"👤 <b>F.I.O:</b> {data['familiya']} {data['ism']} {data['ota_ismi']}\n"
        f"⚧ <b>Jinsi:</b> {data['jins']}\n"
        f"📅 <b>Tug'ilgan sana:</b> {data['tugilgan_kun']}\n"
        f"📞 <b>Telefon:</b> {data['telefon']}\n"
        f"📍 <b>Manzil:</b> {data['viloyat']}, {data['tuman']}\n"
        f"🏫 <b>Maktab:</b> {data['maktab']}\n"
        f"🎒 <b>Sinf:</b> {data['sinf']}-sinf\n"
        f"📚 <b>Fan:</b> {data['fan']}\n"
        f"🇺🇿 <b>Til:</b> {data['til']}"
    )
    
    await message.answer_photo(
        photo=photo_id, 
        caption=caption, 
        parse_mode="HTML", 
        reply_markup=inline.confirm_kb
    )
    await state.set_state(RegisterState.confirm)

@router.message(RegisterState.photo)
async def photo_error(message: types.Message):
    await message.answer("❌ Iltimos, faqat rasm yuboring!")

# 14. Tasdiqlash -> TO'LOV INFO VA CHEK
@router.message(RegisterState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    
    data = await state.get_data()
    
    caption = (
        f"<b>📋 MA'LUMOTLARNI TEKSHIRING:</b>\n\n"
        f"👤 <b>F.I.O:</b> {data['familiya']} {data['ism']} {data['ota_ismi']}\n"
        f"📅 <b>Tug'ilgan sana:</b> {data['tugilgan_kun']}\n"
        f"📞 <b>Telefon:</b> {data['telefon']}\n"
        f"🏫 <b>Maktab:</b> {data['maktab']} ({data['sinf']}-sinf)\n"
        f"📚 <b>Fan:</b> {data['fan']}\n"
        f"📍 <b>Manzil:</b> {data['viloyat']}, {data['tuman']}\n"
    )
    
    await message.answer_photo(
        photo=photo_id, 
        caption=caption, 
        parse_mode="HTML", 
        reply_markup=inline.confirm_kb
    )
    await state.set_state(RegisterState.confirm)

@router.message(RegisterState.photo)
async def photo_error(message: types.Message):
    await message.answer("❌ Iltimos, faqat rasm yuboring!")

# 14. Tasdiqlash -> TO'LOV INFO
@router.callback_query(RegisterState.confirm)
async def process_confirm_step(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "confirm":
        await callback.message.delete()
        
        payment_info = (
            "✅ <b>Ma'lumotlaringiz qabul qilindi!</b>\n\n"
            "🏆 <b>\"ZUKKO MATEMATIK-2026\"</b> tanlovida qatnashish uchun to'lovni amalga oshiring.\n\n"
            "💳 <b>Karta raqam:</b> <code>9860120160864613</code>\n"
            "👤 <b>Karta egasi:</b> TEMUR KENJAYEV\n"
            "💰 <b>To'lov summasi:</b> 95 000 so'm\n\n"
            "📲 <b>To'lov turlari:</b> CLICK, PAYME, OSON, PAYNET, APELSIN va boshqalar orqali.\n\n"
            "📅 <b>Qabul muddati:</b> 25-yanvar sanasigacha\n\n"
            "📞 <b>Murojaat uchun:</b>\n"
            "<b>+998 95 778 21 00</b>\n"
            "<b>+998 93 636 56 00</b>\n\n"
            "📸 <b>Iltimos, to'lov qilganingiz haqidagi chekni (skrinshot) shu yerga yuboring:</b>"
        )
        await callback.message.answer(payment_info, parse_mode="HTML")
        await state.set_state(RegisterState.check)
        
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Ro'yxatdan o'tish bekor qilindi. /start ni bosing.")
        await state.clear()

# ==========================================
# 🏁 3. YAKUNIY QISM (PROFESSIONAL VARIANT)
# ==========================================
@router.message(RegisterState.check, F.photo)
async def process_check_final(message: types.Message, state: FSMContext, bot: Bot):
    # 1. Chek rasmini olamiz
    check_id = message.photo[-1].file_id
    await state.update_data(check=check_id) 
    
    data = await state.get_data()
    user = message.from_user
    
    # Hozirgi vaqtni olamiz
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Username va Link
    if user.username:
        user_link = f"https://t.me/{user.username}"
        username_text = f"@{user.username}"
    else:
        user_link = f"tg://user?id={user.id}"
        username_text = "Mavjud emas"
    
    # 2. Bazaga saqlash
    try:
        await add_user(data, user.id)
    except Exception as e:
        print(f"Baza xatosi: {e}")

    # ------------------------------------------------
    # 📤 GURUHGA YUBORISH (2 QISMLI XABAR)
    # ------------------------------------------------
    
    # A) 1-XABAR: O'quvchi rasmi va ma'lumotlari
    anketa_caption = (
        f"🆕 <b>YANGI ARIZA QABUL QILINDI!</b>\n\n"
        f"👤 <b>Ism-Familiya:</b> {data['familiya']} {data['ism']} {data['ota_ismi']}\n"
        f"📞 <b>Telefon:</b> {data['telefon']}\n"
        f"📅 <b>Tug'ilgan sana:</b> {data['tugilgan_kun']}\n"
        f"📍 <b>Manzil:</b> {data['viloyat']}, {data['tuman']}\n"
        f"🏫 <b>Maktab:</b> {data['maktab']}\n"
        f"🎒 <b>Sinf:</b> {data['sinf']}-sinf\n"
        f"📚 <b>Fan:</b> {data['fan']}\n"
        f"🇺🇿 <b>Til:</b> {data['til']}\n\n"
        f"🔗 <b>Telegram:</b> <a href='{user_link}'>{username_text}</a>\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🕒 <b>Vaqt:</b> {now}"
    )

    # B) 2-XABAR: Chek rasmi va TUGMALAR
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"check_confirm_{user.id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"check_reject_{user.id}")
        ]
    ])
    
    try:
        # 1. O'quvchi rasmini yuboramiz
        await bot.send_photo(
            chat_id=GROUP_ID,
            photo=data['photo'], # User yuklagan rasm (selfie)
            caption=anketa_caption,
            parse_mode="HTML"
        )
        
        # 2. Chek rasmini yuboramiz (Tugmalar shu yerda bo'ladi)
        await bot.send_photo(
            chat_id=GROUP_ID,
            photo=check_id, # Chek rasmi
            caption=f"📄 <b>{data['ism']} {data['familiya']}</b>ning to'lov cheki (95 000 so'm)",
            parse_mode="HTML",
            reply_markup=admin_kb
        )
        
        # Userga javob
        await message.answer(
            "✅ <b>Ariza muvaffaqiyatli yuborildi!</b>\n\n"
            "Hozirda adminlar sizning to'lov chekingizni tekshirmoqda.\n"
            "Tasdiqlangandan so'ng sizga shu bot orqali xabar keladi.\n\n"
            "<i>Iltimos, kuting...</i>",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
    except Exception as e:
        print(f"GURUHGA YUBORISHDA XATO: {e}")
        await message.answer("✅ Ariza qabul qilindi.")

    await state.clear()

@router.message(RegisterState.check)
async def check_error(message: types.Message):
    await message.answer("⚠️ Iltimos, faqat chek rasmini (skrinshot) yuboring.")