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
    btn3 = types.KeyboardButton("ГПР")

    keyboard.row(btn1, btn2)
    keyboard.row(btn3)
    return keyboard

def get_work_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Начать работу")
    btn2 = types.KeyboardButton("Внести данные")
    btn3 = types.KeyboardButton("Гпp")
    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)
    return keyboard

def get_director_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Просрочки")
    keyboard.row(btn1)
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

def get_objects_keyboard_with_back():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    objects = Object.objects.all()
    for obj in objects:
        keyboard.add(types.KeyboardButton(obj.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_workers_keyboard(selected_workers):
    workers = TelegramUser.objects.filter(department='work').exclude(id__in=[worker.id for worker in selected_workers])
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for worker in workers:
        keyboard.add(types.KeyboardButton(worker.first_name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_workers_confirmation_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Подтвердить"))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_back_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_confirmation_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Да"))
    keyboard.add(types.KeyboardButton("Нет"))
    return keyboard

def get_objects_keyboard_for_distribution(user):
    objects = Object.objects.filter(responsible_person=user)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for obj in objects:
        keyboard.add(types.KeyboardButton(obj.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_constructions_keyboard(object_name):
    constructions = Construction.objects.filter(object__name=object_name)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for construction in constructions:
        keyboard.add(types.KeyboardButton(construction.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_stages_keyboard(selected_construction):
    stages = Stage.objects.filter(construction=selected_construction)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for stage in stages:
        keyboard.add(types.KeyboardButton(stage.name))
    keyboard.add(types.KeyboardButton("Назад"))
    return keyboard

def get_gpr_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Сколько осталось")
    btn2 = types.KeyboardButton("Сколько выполнено")
    btn3 = types.KeyboardButton("Ежедневные отчеты")
    btn_back = types.KeyboardButton("Назад")
    keyboard.row(btn1, btn2)
    keyboard.row(btn3)
    keyboard.row(btn_back)
    return keyboard