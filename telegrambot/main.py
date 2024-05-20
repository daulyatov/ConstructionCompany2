import logging
import telebot
from django.conf import settings
from .models import Object, Construction, Stage, TelegramUser
from .keyboards import get_keyboard, get_back_keyboard, get_objects_keyboard, get_constructions_keyboard
from django.core.exceptions import ObjectDoesNotExist

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

bot = telebot.TeleBot(settings.TOKENBOT, parse_mode="HTML")

@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    
    model_user, created = TelegramUser.objects.get_or_create(user_id=user.id)
    
    if created:
        model_user.user_id = user.id
        model_user.username = user.username
        model_user.first_name = user.first_name
        model_user.last_name = user.last_name
        model_user.save()
 
        logging.info(f'Был создан новый аккаунт {model_user.get_name()}')
    
    bot.send_message(message.chat.id, f"Привет, {model_user.get_name()}!", reply_markup=get_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == "добавить объект")
def add_object(message):
    user = message.from_user
    model_user = TelegramUser.objects.get(user_id=user.id)

    bot.send_message(message.chat.id, "Введите название нового объекта:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(message, save_object)

def save_object(message):
    user = message.from_user
    model_user = TelegramUser.objects.get(user_id=user.id)

    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление объекта отменено.", reply_markup=get_keyboard())
        return

    new_object = Object(name=message.text)
    new_object.save()

    bot.send_message(message.chat.id, f"Объект '{new_object.name}' успешно добавлен", reply_markup=get_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == "добавить конструкцию")
def add_construction(message):
    bot.send_message(message.chat.id, "Выберите объект, к которому нужно добавить конструкцию:", reply_markup=get_objects_keyboard())
    bot.register_next_step_handler(message, get_object_for_construction)

def get_object_for_construction(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text)
        bot.send_message(message.chat.id, f"Выбран объект: {selected_object.name}. Введите название новой конструкции:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, get_object_for_construction)

def save_construction(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_keyboard())
        return

    construction_name = message.text
    bot.send_message(message.chat.id, "Введите площадь конструкции в квадратных метрах:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(message, save_construction_area, selected_object, construction_name)

def save_construction_area(message, selected_object, construction_name):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_keyboard())
        return

    try:
        area = int(message.text)
        new_construction = Construction(object=selected_object, name=construction_name, area=area)
        new_construction.save()
        bot.send_message(message.chat.id, f"Конструкция '{new_construction.name}' с площадью {new_construction.area} м² успешно добавлена к объекту '{selected_object.name}'.", reply_markup=get_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное значение площади в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction_area, selected_object, construction_name)

@bot.message_handler(func=lambda message: message.text.lower() == "добавить этап")
def add_stage(message):
    bot.send_message(message.chat.id, "Выберите объект, к которому нужно добавить этап:", reply_markup=get_objects_keyboard())
    bot.register_next_step_handler(message, select_object_for_stage)

def select_object_for_stage(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text)
        bot.send_message(message.chat.id, f"Выбран объект: {selected_object.name}. Выберите конструкцию:", reply_markup=get_constructions_keyboard(selected_object.name))
        bot.register_next_step_handler(message, select_construction_for_stage, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_object_for_stage)

def select_construction_for_stage(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_keyboard())
        return

    try:
        selected_construction = Construction.objects.get(object=selected_object, name=message.text)
        existing_stages = Stage.objects.filter(construction=selected_construction)
        
        if existing_stages:
            stages_list = "\n".join([f"{i + 1}. {stage.name} ({stage.volume} м²)" for i, stage in enumerate(existing_stages)])
            bot.send_message(message.chat.id, f"В выбранной конструкции уже есть следующие этапы:\n{stages_list}")
        
        bot.send_message(message.chat.id, f"Введите название нового этапа для конструкции '{selected_construction.name}':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_stage, selected_construction)
    except Construction.DoesNotExist:
        bot.send_message(message.chat.id, "Конструкция не найдена. Введите корректное название конструкции или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_construction_for_stage, selected_object)

def save_stage(message, selected_construction):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_keyboard())
        return

    stage_name = message.text
    bot.send_message(message.chat.id, "Введите объем этапа в квадратных метрах:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, selected_construction.area)

def save_stage_volume(message, selected_construction, stage_name, max_volume):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_keyboard())
        return

    try:
        volume = int(message.text)
        if volume > max_volume:
            bot.send_message(message.chat.id, f"Объем этапа не может превышать площадь конструкции ({max_volume} м²). Пожалуйста, введите корректное значение объема в квадратных метрах:", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, max_volume)
        else:
            new_stage = Stage(construction=selected_construction, name=stage_name, volume=volume)
            new_stage.save()
            bot.send_message(message.chat.id, f"Этап '{new_stage.name}' с объемом {new_stage.volume} м² успешно добавлен к конструкции '{selected_construction.name}'.", reply_markup=get_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное значение объема в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, max_volume)

def RunBot():
    try:
        logger = logging.getLogger("RunBot")
        logger.info("Запуск бота!")
        bot.polling(none_stop=True, interval=0)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}!")
        raise e
    
    except KeyboardInterrupt:
        logger.info("Бот остановлен принудительно!")
    
    finally:
        logger.info("Завершение работы бота!")
