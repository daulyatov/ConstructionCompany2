from telebot import types
from .models import Object, Construction

def get_contract_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Добавить объект")
    btn2 = types.KeyboardButton("Добавить конструкцию")
    btn3 = types.KeyboardButton("Добавить этап")

    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)

    return keyboard

def get_distribution_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Просмотреть объекты")
    btn2 = types.KeyboardButton("Назначить задачи")
    btn3 = types.KeyboardButton("Отчеты")

    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)

    return keyboard

def get_work_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Начать работу")
    btn2 = types.KeyboardButton("Закончить работу")
    btn3 = types.KeyboardButton("Отправить отчет")

    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)

    return keyboard

def get_back_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("Назад")
    keyboard.add(btn)
    return keyboard

def get_objects_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    objects = Object.objects.all()
    for obj in objects:
        keyboard.add(types.KeyboardButton(obj.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_constructions_keyboard(object_name):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    constructions = Construction.objects.filter(object__name=object_name)
    for construction in constructions:
        keyboard.add(types.KeyboardButton(construction.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard
