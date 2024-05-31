from telebot import types
from .models import Object, Construction, Stage, TelegramUser

def get_contract_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Добавить объект")
    btn2 = types.KeyboardButton("Добавить конструкцию")
    btn3 = types.KeyboardButton("Добавить этап")
    btn4 = types.KeyboardButton("Отчет")
    btn5 = types.KeyboardButton("Назначить ответственного")

    keyboard.row(btn1, btn3)
    keyboard.row(btn2, btn5)
    keyboard.row(btn4)

    return keyboard

def get_distribution_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Назначить рабочего")
    btn2 = types.KeyboardButton("Список назначений")

    keyboard.row(btn1, btn2)
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

def get_objects_keyboard_for_distribution(user):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user.department == 'distribution':
        objects = Object.objects.filter(responsible_person=user)
    else:
        objects = Object.objects.all()

    for obj in objects:
        keyboard.add(types.KeyboardButton(obj.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard



def get_stages_keyboard(construction):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    stages = Stage.objects.filter(construction=construction)
    for stage in stages:
        keyboard.add(types.KeyboardButton(stage.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_workers_keyboard(selected_workers):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    workers = TelegramUser.objects.filter(department='work')
    for worker in workers:
        if worker not in selected_workers:
            keyboard.add(types.KeyboardButton(worker.first_name))
    keyboard.add(types.KeyboardButton("Подтвердить"))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_confirmation_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Да"))
    keyboard.add(types.KeyboardButton("Нет"))
    return keyboard