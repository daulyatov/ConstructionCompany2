from telebot import types


def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Добавить объект")
    btn2 = types.KeyboardButton("Добавить конструкцию")
    btn3 = types.KeyboardButton("Добавить этап")

    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)

    return keyboard

def get_back_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_back = types.KeyboardButton("Назад")
    keyboard.add(btn_back)
    return keyboard
