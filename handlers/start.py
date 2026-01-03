from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from states.register_state import RegisterState
# 👇 O'ZGARISH: ADMIN_ID o'rniga ADMIN_LIST
from config import CHANNEL_ID, CHANNEL_LINK, ADMIN_LIST 
from keyboards.reply import admin_panel 



router = Router()

# ==========================================
# 🛠 YORDAMCHI FUNKSIYA: KANALNI TEKSHIRISH
# ==========================================
async def check_subscription(user_id: int, bot: Bot) -> bool:
    if not CHANNEL_ID:
        return True 
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True 

# ==========================================
# 🚀 /START KOMANDASI
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    # 1. Holatni tozalaymiz
    await state.clear()
    user_id = message.from_user.id
    
    # 2. 🔥 ADMIN TEKSHIRUVI (YANGILANDI)
    # Adminlar ro'yxatida borligini tekshiramiz
    if ADMIN_LIST and user_id in ADMIN_LIST:
        await message.answer("👋 Salom Admin!", reply_markup=admin_panel)
        return
    

    # 3. KANALNI TEKSHIRISH
    is_subscribed = await check_subscription(user_id, bot)
    
    if not is_subscribed:
        # ❌ A'ZO EMAS: Faqat tugma chiqaramiz va TO'XTAYMIZ (return)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="verify_sub")] 
        ])
        
        await message.answer(
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Botdan foydalanish uchun iltimos, rasmiy kanalimizga a'zo bo'ling.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return # ⛔️ SHU YERDA TO'XTAYDI

    # ✅ A'ZO BO'LSA: Darhol familiya so'raymiz
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "\"ZUKKO MATEMATIK-2025\" tanlovining ro'yxatga olish botiga xush kelibsiz.\n"
        "✍️ <b>Familiyangizni kiriting:</b>",
        parse_mode="HTML"
    )
    await state.set_state(RegisterState.familiya)

@router.message(Command("dasturchi"))
async def dev_handler(message: Message):
    text = (
        "👨‍💻 <b>Dasturchi haqida ma'lumot</b>\n\n"
        "Ushbu bot <b>Avazbek (@avazcoder_uz)</b> tomonidan yaratilgan.\n\n"
        "🚀 Agar siz ham shunday botlar yaratishni, Telegram botlar yozishni yoki "
        "dasturlashni o'rganmoqchi bo'lsangiz, quyidagi profilga yozing!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍💻 Dasturchi Profili", url="https://t.me/avazcoder_uz")],
        ]
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

# ==========================================
# 🔄 "A'ZO BO'LDIM" TUGMASI BOSILGANDA
# ==========================================
@router.callback_query(F.data == "verify_sub")
async def process_check_sub(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    # Qayta tekshiramiz
    is_subscribed = await check_subscription(callback.from_user.id, bot)
    
    if is_subscribed:
        # ✅ A'ZO BO'LDI
        await callback.message.delete() # Eski xabarni o'chiramiz
        
        await callback.message.answer(
            "✅ <b>Rahmat!</b> Kanalga a'zo bo'ldingiz.\n\n"
            "Endi ro'yxatdan o'tishimiz mumkin.\n"
            "✍️ <b>Familiyangizni kiriting:</b>",
            parse_mode="HTML"
        )
        await state.set_state(RegisterState.familiya)
    else:
        # ❌ HALI HAM A'ZO EMAS
        await callback.answer(
            "❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, avval a'zo bo'ling.", 
            show_alert=True 
        )