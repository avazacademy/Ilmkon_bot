from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
    resize_keyboard=True, one_time_keyboard=True
)

 

admin_panel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="📢 Reklama yuborish")], # YANGI TUGMA
        [KeyboardButton(text="🔙 Chiqish")]
    ],
    resize_keyboard=True
)