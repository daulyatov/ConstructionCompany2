from telebot import types

from telegrambot.models import Object

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

def get_objects_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    objects = Object.objects.all()
    for obj in objects:
        keyboard.add(types.KeyboardButton(obj.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_constructions_keyboard(object_name):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    obj = Object.objects.get(name=object_name)
    constructions = obj.constructions.all()
    for construction in constructions:
        keyboard.add(types.KeyboardButton(construction.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard
