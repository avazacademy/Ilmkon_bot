from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Jins
jins_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👨 O`g`il bola", callback_data="Erkak"), 
     InlineKeyboardButton(text="👩 Qiz bola", callback_data="Ayol")]
])

# Faqat Surxondaryo viloyati
viloyat_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Surxondaryo viloyati", callback_data="Surxondaryo viloyati")]
])

# Surxondaryo tumanlari (Barchasi)
tuman_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Termiz shahri", callback_data="Termiz shahri"),
     InlineKeyboardButton(text="Termiz tumani", callback_data="Termiz tumani")],
    [InlineKeyboardButton(text="Angor", callback_data="Angor"),
     InlineKeyboardButton(text="Boysun", callback_data="Boysun")],
    [InlineKeyboardButton(text="Denov", callback_data="Denov"),
     InlineKeyboardButton(text="Jarqo'rg'on", callback_data="Jarqo'rg'on")],
    [InlineKeyboardButton(text="Muzrabot", callback_data="Muzrabot"),
     InlineKeyboardButton(text="Oltinsoy", callback_data="Oltinsoy")],
    [InlineKeyboardButton(text="Qiziriq", callback_data="Qiziriq"),
     InlineKeyboardButton(text="Qumqo'rg'on", callback_data="Qumqo'rg'on")],
    [InlineKeyboardButton(text="Sariosiyo", callback_data="Sariosiyo"),
     InlineKeyboardButton(text="Sherobod", callback_data="Sherobod")],
    [InlineKeyboardButton(text="Sho'rchi", callback_data="Sho'rchi"),
     InlineKeyboardButton(text="Uzun", callback_data="Uzun")]
])

# Sinflar
sinf_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="2-sinf", callback_data="2"),
     InlineKeyboardButton(text="3-sinf", callback_data="3")],
    [InlineKeyboardButton(text="4-sinf", callback_data="4"),
     InlineKeyboardButton(text="5-sinf", callback_data="5")],
    [InlineKeyboardButton(text="6-sinf", callback_data="6"),
     InlineKeyboardButton(text="7-sinf", callback_data="7")]
])

# Tillar
lang_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="O'zbekcha"),
     InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="Ruscha")]
])

# Tasdiqlash
confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm"),
     InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
])