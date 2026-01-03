from aiogram.fsm.state import State, StatesGroup

class RegisterState(StatesGroup):
    familiya = State()
    ism = State()
    ota_ismi = State()
    jins = State()
    tugilgan_kun = State()
    telefon = State()
    viloyat = State()
    tuman = State()
    maktab = State()
    sinf = State()
    fan = State()
    til = State()
    photo = State()
    confirm = State() # 1. Tasdiqlash
    check = State()   # 2. Keyin Chek yuklash
    
class AdminState(StatesGroup):
    waiting_for_ad = State()  # Reklama xabarini kutish