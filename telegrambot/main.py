import logging
import telebot
from telebot import types
from django.conf import settings
import datetime
from datetime import timedelta
from django.utils import timezone
from .models import Object, Construction, Stage, TelegramUser, DailyReport, CompletedWork, Underperformance
from .keyboards import get_back_keyboard, get_contract_keyboard, get_director_keyboard, get_distribution_keyboard, get_objects_keyboard,get_gpr_keyboard, \
            get_constructions_keyboard, get_work_keyboard, get_objects_keyboard_for_distribution, get_stages_keyboard, get_confirmation_keyboard, get_workers_confirmation_keyboard, get_workers_keyboard, get_objects_keyboard_with_back

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
        ask_for_department(message)
    else:
        bot.send_message(message.chat.id, f"Привет, {model_user.get_name()}!", reply_markup=get_keyboard_by_department(model_user.department))

def ask_for_department(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("Договорной отдел"))
    keyboard.add(types.KeyboardButton("Отдел распределения"))
    keyboard.add(types.KeyboardButton("Рабочий отдел"))
    keyboard.add(types.KeyboardButton("Директор"))

    bot.send_message(message.chat.id, "Выберите свой отдел:", reply_markup=keyboard)
    bot.register_next_step_handler(message, save_department)

def save_department(message):
    department_map = {
        "Договорной отдел": "contract",
        "Отдел распределения": "distribution",
        "Рабочий отдел": "work",
        "Директор": "director"
    }

    user = message.from_user
    model_user = TelegramUser.objects.get(user_id=user.id)
    
    department = department_map.get(message.text)
    
    if department:
        model_user.department = department
        model_user.save()
        bot.send_message(message.chat.id, f"Вы выбрали {message.text}.", reply_markup=get_keyboard_by_department(department))
    else:
        bot.send_message(message.chat.id, "Неверный выбор. Пожалуйста, выберите отдел.", reply_markup=ask_for_department(message))

def get_keyboard_by_department(department):
    if department == "contract":
        return get_contract_keyboard()
    elif department == "distribution":
        return get_distribution_keyboard()
    elif department == "work":
        return get_work_keyboard()
    elif department == "director":
        return get_director_keyboard()
    else:
        return types.ReplyKeyboardMarkup(resize_keyboard=True)



# договорной отдел
@bot.message_handler(func=lambda message: message.text.lower() == "добавить объект")
def add_object(message):
    user = message.from_user
    model_user = TelegramUser.objects.get(user_id=user.id)

    bot.send_message(message.chat.id, "Введите название нового объекта:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(message, save_object)

def save_object(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление объекта отменено.", reply_markup=get_contract_keyboard())
        return

    if Object.objects.filter(name=message.text).exists():
        bot.send_message(message.chat.id, "Объект с таким названием уже существует. Введите другое название:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_object)
    else:
        new_object = Object(name=message.text)
        new_object.save()
        bot.send_message(message.chat.id, f"Объект '{new_object.name}' успешно добавлен", reply_markup=get_contract_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == "добавить конструкцию")
def add_construction(message):
    bot.send_message(message.chat.id, "Выберите объект, к которому нужно добавить конструкцию:", reply_markup=get_objects_keyboard())
    bot.register_next_step_handler(message, get_object_for_construction)

def get_object_for_construction(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text)
        constructions = Construction.objects.filter(object=selected_object)
        
        if constructions.exists():
            constructions_message = "<b>Существующие конструкции:</b>\n"
            for constr in constructions:
                constructions_message += f"  - <b>{constr.name}</b> (площадь: {constr.area} м²)\n"
            bot.send_message(message.chat.id, constructions_message, parse_mode="HTML")
        
        bot.send_message(message.chat.id, f"Выбран объект: {selected_object.name}. Введите название новой конструкции:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, get_object_for_construction)

def save_construction(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_contract_keyboard())
        return

    if Construction.objects.filter(object=selected_object, name=message.text).exists():
        bot.send_message(message.chat.id, "Конструкция с таким названием уже существует в данном объекте. Введите другое название:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction, selected_object)
    else:
        construction_name = message.text
        bot.send_message(message.chat.id, "Введите площадь конструкции в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction_area, selected_object, construction_name)

def save_construction_area(message, selected_object, construction_name):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление конструкции отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        area = int(message.text)
        new_construction = Construction(object=selected_object, name=construction_name, area=area)
        new_construction.save()
        bot.send_message(message.chat.id, f"Конструкция '{new_construction.name}' с площадью {new_construction.area} м² успешно добавлена к объекту '{selected_object.name}'.", reply_markup=get_contract_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное значение площади в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_construction_area, selected_object, construction_name)

@bot.message_handler(func=lambda message: message.text.lower() == "добавить этап")
def add_stage(message):
    bot.send_message(message.chat.id, "Выберите объект, к которому нужно добавить этап:", reply_markup=get_objects_keyboard())
    bot.register_next_step_handler(message, select_object_for_stage)

def select_object_for_stage(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text)
        constructions = Construction.objects.filter(object=selected_object)
        
        if constructions.exists():
            constructions_message = "<b>Существующие конструкции:</b>\n"
            for constr in constructions:
                constructions_message += f"  - <b>{constr.name}</b> (площадь: {constr.area} m²)\n"
            bot.send_message(message.chat.id, constructions_message, parse_mode="HTML")
        
        bot.send_message(message.chat.id, f"Выбран объект: <b>{selected_object.name}</b>. Выберите конструкцию:", reply_markup=get_constructions_keyboard(selected_object.name), parse_mode="HTML")
        bot.register_next_step_handler(message, select_construction_for_stage, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_object_for_stage)

def select_construction_for_stage(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        selected_construction = Construction.objects.get(object=selected_object, name=message.text)
        existing_stages = Stage.objects.filter(construction=selected_construction)
        
        if existing_stages:
            stages_list = "\n".join([f"{i + 1}. <b>{stage.name}</b> ({stage.volume} m²)" for i, stage in enumerate(existing_stages)])
            bot.send_message(message.chat.id, f"В выбранной конструкции уже есть следующие этапы:\n{stages_list}", parse_mode="HTML")
        
        bot.send_message(message.chat.id, f"Введите название нового этапа для конструкции '<b>{selected_construction.name}</b>':", reply_markup=get_back_keyboard(), parse_mode="HTML")
        bot.register_next_step_handler(message, save_stage, selected_construction)
    except Construction.DoesNotExist:
        bot.send_message(message.chat.id, "Конструкция не найдена. Введите корректное название конструкции или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_construction_for_stage, selected_object)

def save_stage(message, selected_construction):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_contract_keyboard())
        return

    if Stage.objects.filter(construction=selected_construction, name=message.text).exists():
        bot.send_message(message.chat.id, "Этап с таким названием уже существует в данной конструкции. Введите другое название:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_stage, selected_construction)
    else:
        stage_name = message.text
        bot.send_message(message.chat.id, "Введите объем этапа в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, selected_construction.area)

def save_stage_volume(message, selected_construction, stage_name, max_volume):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Добавление этапа отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        volume = int(message.text)
        if volume > max_volume:
            bot.send_message(message.chat.id, f"Объем этапа не может превышать площадь конструкции ({max_volume} м²). Пожалуйста, введите корректное значение объема в квадратных метрах:", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, max_volume)
        else:
            new_stage = Stage(construction=selected_construction, name=stage_name, volume=volume)
            new_stage.save()
            bot.send_message(message.chat.id, f"Этап '<b>{new_stage.name}</b>' с объемом {new_stage.volume} м² успешно добавлен к конструкции '<b>{selected_construction.name}</b>'.", reply_markup=get_contract_keyboard(), parse_mode="HTML")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное значение объема в квадратных метрах:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_stage_volume, selected_construction, stage_name, max_volume)

@bot.message_handler(func=lambda message: message.text.lower() == "назначить ответственного")
def assign_responsible(message):
    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=get_objects_keyboard_with_back())
    bot.register_next_step_handler(message, select_object_for_responsible)

def select_object_for_responsible(message):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение ответственного отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text)
        distribution_users = TelegramUser.objects.filter(department='distribution')

        if distribution_users.exists():
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for user in distribution_users:
                keyboard.add(types.KeyboardButton(user.first_name))
            keyboard.add(types.KeyboardButton("Назад"))

            bot.send_message(message.chat.id, "Выберите ответственного:", reply_markup=keyboard)
            bot.register_next_step_handler(message, save_responsible, selected_object)
        else:
            bot.send_message(message.chat.id, "Нет пользователей в отделе распределения.", reply_markup=get_contract_keyboard())
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_object_for_responsible)

def save_responsible(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение ответственного отменено.", reply_markup=get_contract_keyboard())
        return

    try:
        responsible_user = TelegramUser.objects.get(first_name=message.text, department='distribution')
        selected_object.responsible_person = responsible_user
        selected_object.save()
        bot.send_message(message.chat.id, f"Пользователь {responsible_user.first_name} назначен ответственным за объект '{selected_object.name}'.", reply_markup=get_contract_keyboard())
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Пользователь не найден или не принадлежит к отделу распределения. Введите корректное имя пользователя или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_responsible, selected_object)

@bot.message_handler(func=lambda message: message.text.lower() == "отчет")
def send_report(message):
    user = message.from_user
    model_user = TelegramUser.objects.get(user_id=user.id)

    objects = Object.objects.all()
    if not objects:
        bot.send_message(message.chat.id, "У вас нет объектов.", reply_markup=get_contract_keyboard())
        return
    
    report_message = "<b>Ваши объекты:</b>\n\n" 
    for i, obj in enumerate(objects, 1):
        responsible = obj.responsible_person.first_name if obj.responsible_person else "Нет ответственного"
        report_message += f"<b>{i}. Объект: {obj.name}</b> (Ответственный: <b>{responsible}</b>)\n"
        constructions = Construction.objects.filter(object=obj)
        if constructions:
            report_message += "  <b>Конструкции:</b>\n"
            for constr in constructions:
                report_message += f"    - <b>{constr.name}</b> (площадь: {constr.area} м²)\n"
                stages = Stage.objects.filter(construction=constr)
                if stages:
                    report_message += "      <b>Этапы:</b>\n"
                    for stage in stages:
                        report_message += f"        * <b>{stage.name}</b> (объем: {stage.volume} м²)\n"
        else:
            report_message += "  <b>Нет конструкций.</b>\n"
        report_message += "\n"

    bot.send_message(message.chat.id, report_message, parse_mode="HTML", reply_markup=get_contract_keyboard())


# Отдел распределения
user_sessions = {}

@bot.message_handler(func=lambda message: message.text.lower() == "назначить рабочего")
def assign_worker(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    if user.department != 'distribution':
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    user_sessions[message.chat.id] = {'selected_worker': None}

    assigned_objects = Object.objects.filter(responsible_person=user)
    if assigned_objects.exists():
        bot.send_message(message.chat.id, "Выберите объект:", reply_markup=get_objects_keyboard_for_distribution(user))
        bot.register_next_step_handler(message, select_object_for_worker_assignment)
    else:
        bot.send_message(message.chat.id, "Вам не назначен ни один объект.")
        user_sessions.pop(message.chat.id, None)

def select_object_for_worker_assignment(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        selected_object = Object.objects.get(name=message.text, responsible_person=user)
        user_sessions[message.chat.id]['selected_object'] = selected_object
        bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=get_constructions_keyboard(selected_object.name))
        bot.register_next_step_handler(message, select_construction_for_worker_assignment, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден или у вас нет прав доступа к этому объекту. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_object_for_worker_assignment)

def select_construction_for_worker_assignment(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        selected_construction = Construction.objects.get(object=selected_object, name=message.text)
        user_sessions[message.chat.id]['selected_construction'] = selected_construction
        stages = Stage.objects.filter(construction=selected_construction)
        if not stages.exists():
            bot.send_message(message.chat.id, "В этой конструкции нет этапов. Выберите другую конструкцию:", reply_markup=get_constructions_keyboard(selected_object.name))
            bot.register_next_step_handler(message, select_construction_for_worker_assignment, selected_object)
        else:
            bot.send_message(message.chat.id, "Выберите этап:", reply_markup=get_stages_keyboard(selected_construction))
            bot.register_next_step_handler(message, select_stage_for_worker_assignment, selected_construction)
    except Construction.DoesNotExist:
        bot.send_message(message.chat.id, "Конструкция не найдена. Введите корректное название конструкции или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_construction_for_worker_assignment, selected_object)

def select_stage_for_worker_assignment(message, selected_construction):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        selected_stage = Stage.objects.get(construction=selected_construction, name=message.text)
        user_sessions[message.chat.id]['selected_stage'] = selected_stage
        workers = TelegramUser.objects.filter(department='work')
        if not workers.exists():
            bot.send_message(message.chat.id, "Нет рабочих для назначения.", reply_markup=get_distribution_keyboard())
            user_sessions.pop(message.chat.id, None)
            return
        if selected_stage.workers_assigned.exists():
            assigned_workers = selected_stage.workers_assigned.all()
            worker_names = ", ".join([worker.get_name() for worker in assigned_workers])
            bot.send_message(message.chat.id, f"На этапе уже назначены рабочие: {worker_names}. Хотите перезаписать?", reply_markup=get_confirmation_keyboard())
            bot.register_next_step_handler(message, confirm_overwrite_assignment)
        else:
            bot.send_message(message.chat.id, "Выберите рабочего для назначения на этап:", reply_markup=get_workers_keyboard([]))
            bot.register_next_step_handler(message, select_worker_for_stage, selected_stage)
    except Stage.DoesNotExist:
        bot.send_message(message.chat.id, "Этап не найден. Введите корректное название этапа или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_stage_for_worker_assignment, selected_construction)

def confirm_overwrite_assignment(message):
    if message.text.lower() == "да":
        bot.send_message(message.chat.id, "Выберите рабочего для назначения на этап:", reply_markup=get_workers_keyboard([]))
        bot.register_next_step_handler(message, select_worker_for_stage, user_sessions[message.chat.id]['selected_stage'])
    elif message.text.lower() == "нет":
        bot.send_message(message.chat.id, "Выберите этап:", reply_markup=get_stages_keyboard(user_sessions[message.chat.id]['selected_construction']))
        bot.register_next_step_handler(message, select_stage_for_worker_assignment, user_sessions[message.chat.id]['selected_construction'])
    else:
        bot.send_message(message.chat.id, "Неверный ввод. Пожалуйста, выберите 'Да' или 'Нет'.", reply_markup=get_confirmation_keyboard())
        bot.register_next_step_handler(message, confirm_overwrite_assignment)

def select_worker_for_stage(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    if message.text.lower() == "подтвердить":
        selected_worker = user_sessions[message.chat.id]['selected_worker']
        if not selected_worker:
            bot.send_message(message.chat.id, "Вы не выбрали ни одного рабочего. Пожалуйста, выберите рабочего и нажмите 'Подтвердить'.", reply_markup=get_workers_keyboard([]))
            bot.register_next_step_handler(message, select_worker_for_stage, selected_stage)
        else:
            bot.send_message(message.chat.id, "Введите количество рабочих:", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, enter_number_of_workers, selected_stage)
        return

    worker_name = message.text
    try:
        worker = TelegramUser.objects.get(first_name=worker_name, department='work')
        user_sessions[message.chat.id]['selected_worker'] = worker
        bot.send_message(message.chat.id, f"На этап будет назначен рабочий: {worker.get_name()}. Нажмите 'Подтвердить' для сохранения или выберите другого рабочего.", reply_markup=get_workers_confirmation_keyboard())
        bot.register_next_step_handler(message, select_worker_for_stage, selected_stage)
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Рабочий не найден. Попробуйте снова или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_worker_for_stage, selected_stage)

def enter_number_of_workers(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        number_of_workers = int(message.text)
        user_sessions[message.chat.id]['number_of_workers'] = number_of_workers
        bot.send_message(message.chat.id, "Введите дату начала этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, enter_start_date, selected_stage)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Введите количество рабочих числом:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, enter_number_of_workers, selected_stage)

def enter_start_date(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        start_date = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        current_date = timezone.now().replace(tzinfo=None)  # Преобразуем current_date в naive формат

        if start_date < current_date:
            bot.send_message(message.chat.id, "Нельзя назначить прошедшую дату. Введите дату начала этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, enter_start_date, selected_stage)
            return

        user_sessions[message.chat.id]['start_date'] = start_date
        bot.send_message(message.chat.id, "Введите дату окончания этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, enter_end_date, selected_stage)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Введите дату начала этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, enter_start_date, selected_stage)

def enter_end_date(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        end_date = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        start_date = user_sessions[message.chat.id]['start_date']

        if end_date <= start_date:
            bot.send_message(message.chat.id, "Дата окончания должна быть позже даты начала. Введите дату окончания этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, enter_end_date, selected_stage)
            return

        user_sessions[message.chat.id]['end_date'] = end_date
        finalize_worker_assignment(message, selected_stage)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Введите дату окончания этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, enter_end_date, selected_stage)

def finalize_worker_assignment(message, selected_stage):
    worker = user_sessions[message.chat.id]['selected_worker']
    number_of_workers = user_sessions[message.chat.id]['number_of_workers']
    start_date = user_sessions[message.chat.id]['start_date']
    end_date = user_sessions[message.chat.id]['end_date']

    # Assign worker to stage
    selected_stage.workers_assigned.add(worker)
    selected_stage.number_of_workers = number_of_workers
    selected_stage.start_date = start_date
    selected_stage.end_date = end_date
    selected_stage.save()

    bot.send_message(message.chat.id, f"Рабочий {worker.get_name()} назначен на этап '{selected_stage.name}' конструкции '{selected_stage.construction.name}' объекта '{selected_stage.construction.object.name}'.", reply_markup=get_distribution_keyboard())
    user_sessions.pop(message.chat.id, None)

@bot.message_handler(func=lambda message: message.text.lower() == "список назначений")
def show_assignments_list(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    if user.department != 'distribution':
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    assigned_objects = Object.objects.filter(responsible_person=user)

    if not assigned_objects.exists():
        bot.send_message(message.chat.id, "У вас нет назначенных объектов.", reply_markup=get_distribution_keyboard())
        return

    assignments_message = "<b>Список назначений:</b>\n\n"
    for i, obj in enumerate(assigned_objects, 1):
        assignments_message += f"<b>{i}. Объект: {obj.name}</b>\n"
        constructions = Construction.objects.filter(object=obj)
        if constructions.exists():
            for constr in constructions:
                assignments_message += f"  <b>Конструкция: {constr.name}</b>\n"
                stages = Stage.objects.filter(construction=constr)
                if stages.exists():
                    for stage in stages:
                        worker_count = stage.number_of_workers
                        start_date = stage.start_date.strftime("%d.%m.%Y") if stage.start_date else "не установлена"
                        end_date = stage.end_date.strftime("%d.%m.%Y") if stage.end_date else "не установлена"
                        assignments_message += f"    - <b>Этап: {stage.name}</b> (Рабочих: {worker_count}, Дата начала: {start_date}, Дата окончания: {end_date})\n"
                else:
                    assignments_message += "    - <b>Нет этапов.</b>\n"
        else:
            assignments_message += "  <b>Нет конструкций.</b>\n"
        assignments_message += "\n"

    bot.send_message(message.chat.id, assignments_message, parse_mode="HTML", reply_markup=get_distribution_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == "гпр")
def generate_report(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    if user.department != 'distribution':
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    assigned_objects = Object.objects.filter(responsible_person=user)

    if assigned_objects.exists():
        bot.send_message(message.chat.id, "Выберите объект:", reply_markup=get_objects_keyboard_for_distribution(user))
        bot.register_next_step_handler(message, select_object_for_report)
    else:
        bot.send_message(message.chat.id, "Вам не назначен ни один объект.", reply_markup=get_distribution_keyboard())

def select_object_for_report(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Генерация отчета отменена.", reply_markup=get_distribution_keyboard())
        return

    try:
        selected_object = Object.objects.get(name=message.text, responsible_person=user)
        bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=get_constructions_keyboard(selected_object.name))
        bot.register_next_step_handler(message, select_construction_for_report, selected_object)
    except Object.DoesNotExist:
        bot.send_message(message.chat.id, "Объект не найден или у вас нет прав доступа к этому объекту. Введите корректное название объекта или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_object_for_report)

def select_construction_for_report(message, selected_object):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Генерация отчета отменена.", reply_markup=get_distribution_keyboard())
        return

    try:
        selected_construction = Construction.objects.get(object=selected_object, name=message.text)
        bot.send_message(message.chat.id, "Выберите этап:", reply_markup=get_stages_keyboard(selected_construction))
        bot.register_next_step_handler(message, select_stage_for_report, selected_construction)
    except Construction.DoesNotExist:
        bot.send_message(message.chat.id, "Конструкция не найдена. Введите корректное название конструкции или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_construction_for_report, selected_object)

def select_stage_for_report(message, selected_construction):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Генерация отчета отменена.", reply_markup=get_distribution_keyboard())
        return

    try:
        selected_stage = Stage.objects.get(construction=selected_construction, name=message.text)
        total_completed_volume = sum(work.volume for work in selected_stage.completed_works.all())
        remaining_volume = selected_stage.volume - total_completed_volume

        if remaining_volume <= 0:
            report_message = (
                f"<b>Объект:</b> {selected_construction.object.name}\n"
                f"<b>Конструкция:</b> {selected_construction.name}\n"
                f"<b>Этап:</b> {selected_stage.name}\n"
                f"<b>Объем выполненных работ:</b> {total_completed_volume} м²\n"
                f"<b>Статус:</b> Этап успешно выполнен."
            )
        else:
            report_message = (
                f"<b>Объект:</b> {selected_construction.object.name}\n"
                f"<b>Конструкция:</b> {selected_construction.name}\n"
                f"<b>Этап:</b> {selected_stage.name}\n"
                f"<b>Объем выполненных работ:</b> {total_completed_volume} м²\n"
                f"<b>Оставшийся объем:</b> {remaining_volume} м²"
            )

        bot.send_message(message.chat.id, report_message, parse_mode="HTML", reply_markup=get_distribution_keyboard())
    except Stage.DoesNotExist:
        bot.send_message(message.chat.id, "Этап не найден. Введите корректное название этапа или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_stage_for_report, selected_construction)












# Рабочий отдел 
@bot.message_handler(func=lambda message: message.text == "Начать работу")
def start_work(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в рабочем отделе.")
        return

    # Получаем этапы, назначенные пользователю, отсортированные по дате начала и неполные
    assigned_stages = model_user.assigned_stages.filter(
        start_date__isnull=False,
        completed=False
    ).order_by('start_date')

    if not assigned_stages.exists():
        bot.send_message(message.chat.id, "У вас нет назначенных этапов.")
        return

    # Создаем кнопки для этапов
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in assigned_stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    # Отправляем кнопки пользователю
    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, handle_stage_selection)

def handle_stage_selection(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_work_keyboard())
        return

    stage_name = message.text
    try:
        stage = Stage.objects.get(name=stage_name)
    except Stage.DoesNotExist:
        bot.send_message(message.chat.id, "Этап не найден.")
        start_work(message)
        return

    construction = stage.construction
    obj = construction.object
    start_date = stage.start_date
    end_date = stage.end_date

    # Текущая дата
    today = timezone.now().date()

    # Расчет выполненного объема работы
    total_completed_volume = sum(work.volume for work in stage.completed_works.all())

    # Получаем ежедневные отчеты для этапа
    daily_reports = stage.daily_reports.all()
    daily_report_messages = "\n".join([f"{report.date.strftime('%d.%m.%Y')}: Выполнено: {report.completed_volume} м², Рабочих: {report.number_of_workers}" for report in daily_reports])

    # Определяем, начался ли этап
    if today < start_date:
        days_until_start = (start_date - today).days
        total_days = (end_date - start_date).days
        daily_volume_needed = stage.volume / total_days if total_days > 0 else 0
        report_message = (
            f"<b>Объект:</b> {obj.name}\n"
            f"<b>Конструкция:</b> {construction.name}\n"
            f"<b>Этап:</b> {stage.name}\n"
            f"<b>Дата начала:</b> {start_date.strftime('%d.%m.%Y') if start_date else 'не установлена'}\n"
            f"<b>Дата окончания:</b> {end_date.strftime('%d.%m.%Y')}\n"
            f"<b>До начала осталось:</b> {days_until_start} дней\n"
            f"<b>Выполнено:</b> {total_completed_volume} м²\n"
            f"<b>Объем этапа:</b> {stage.volume} м²\n"
            f"<b>Количество рабочих:</b> {stage.number_of_workers}\n"
            f"<b>Нужно выполнять в день:</b> {daily_volume_needed:.1f} м²\n"
            f"<b>Ежедневные отчеты:</b>\n{daily_report_messages}"
        )
    else:
        days_left = (end_date - today).days
        daily_volume_needed = stage.volume / days_left if days_left > 0 else 0
        report_message = (
            f"<b>Объект:</b> {obj.name}\n"
            f"<b>Конструкция:</b> {construction.name}\n"
            f"<b>Этап:</b> {stage.name}\n"
            f"<b>Дата начала:</b> {start_date.strftime('%d.%m.%Y') if start_date else 'не установлена'}\n"
            f"<b>Дата окончания:</б> {end_date.strftime('%d.%м.%Y')}\n"
            f"<b>Осталось:</б> {days_left} дней\n"
            f"<b>Выполнено:</б> {total_completed_volume} м²\n"
            f"<b>Объем этапа:</б> {stage.volume} м²\n"
            f"<b>Количество рабочих:</б> {stage.number_of_workers}\n"
            f"<b>Нужно выполнять в день:</б> {daily_volume_needed:.1f} м²\n"
            f"<b>Ежедневные отчеты:</б>\n{daily_report_messages}"
        )

    # Отправка сообщения пользователю
    bot.send_message(message.chat.id, report_message, parse_mode="HTML", reply_markup=get_work_keyboard())

@bot.message_handler(func=lambda message: message.text == "Внести данные")
def enter_data(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в рабочем отделе.")
        return
    
    # Получаем объекты с незавершенными этапами, назначенными пользователю
    assigned_stages = model_user.assigned_stages.filter(completed=False).order_by('end_date')
    objects_with_stages = {stage.construction.object for stage in assigned_stages}

    if not assigned_stages.exists():
        bot.send_message(message.chat.id, "У вас нет незавершенных этапов.")
        return

    # Создаем кнопки для объектов
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for obj in objects_with_stages:
        reply_markup.add(types.KeyboardButton(obj.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    # Отправляем кнопки пользователю
    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_object_for_data_entry, objects_with_stages, assigned_stages)

def select_object_for_data_entry(message, objects_with_stages, assigned_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_work_keyboard())
        return

    try:
        selected_object = next(obj for obj in objects_with_stages if obj.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Объект не найден.")
        enter_data(message)
        return

    # Получаем конструкции выбранного объекта
    constructions = {stage.construction for stage in assigned_stages if stage.construction.object == selected_object}

    # Создаем кнопки для конструкций
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for construction in constructions:
        reply_markup.add(types.KeyboardButton(construction.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    # Отправляем кнопки пользователю
    bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_construction_for_data_entry, selected_object, constructions, assigned_stages, objects_with_stages)

def select_construction_for_data_entry(message, selected_object, constructions, assigned_stages, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_work_keyboard())
        return

    try:
        selected_construction = next(constr for constr in constructions if constr.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Конструкция не найдена.")
        select_object_for_data_entry(message, objects_with_stages, assigned_stages)
        return

    # Получаем этапы выбранной конструкции
    stages = [stage for stage in assigned_stages if stage.construction == selected_construction]

    # Создаем кнопки для этапов
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    # Отправляем кнопки пользователю
    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_stage_for_data_entry, selected_object, stages, selected_construction, constructions, assigned_stages, objects_with_stages)

def select_stage_for_data_entry(message, selected_object, stages, selected_construction, constructions, assigned_stages, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_work_keyboard())
        return

    try:
        selected_stage = next(stage for stage in stages if stage.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Этап не найден.")
        select_construction_for_data_entry(message, selected_object, constructions, assigned_stages, objects_with_stages)
        return

    # Сохраняем выбранный этап в сессии пользователя
    user_sessions[message.chat.id] = selected_stage

    # Запрашиваем количество рабочих и объем выполненных работ у пользователя
    bot.send_message(message.chat.id, "Введите количество рабочих:")
    bot.register_next_step_handler(message, get_number_of_workers)

def get_number_of_workers(message):
    try:
        number_of_workers = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Введите количество рабочих числом:")
        bot.register_next_step_handler(message, get_number_of_workers)
        return

    user_sessions[message.chat.id].number_of_workers_today = number_of_workers
    bot.send_message(message.chat.id, "Введите объем выполненных работ (в м²):")
    bot.register_next_step_handler(message, get_completed_volume)

def get_completed_volume(message):
    try:
        completed_volume = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Введите объем выполненных работ числом:")
        bot.register_next_step_handler(message, get_completed_volume)
        return

    try:
        selected_stage = user_sessions.pop(message.chat.id)
        number_of_workers = selected_stage.number_of_workers_today

        # Сохраняем данные в базу данных
        CompletedWork.objects.create(
            stage=selected_stage,
            volume=completed_volume,
            date=timezone.now().date()
        )

        DailyReport.objects.create(
            stage=selected_stage,
            number_of_workers=number_of_workers,
            completed_volume=completed_volume
        )

        # Пересчитываем оставшийся объем
        total_completed_volume = sum(work.volume for work in selected_stage.completed_works.all())
        remaining_volume = selected_stage.volume - total_completed_volume

        # Логика для создания просрочек
        today = timezone.now().date()
        total_days = (selected_stage.end_date - selected_stage.start_date).days or 1
        daily_volume_needed = selected_stage.volume / total_days

        volume_deficit = daily_volume_needed - completed_volume if completed_volume < daily_volume_needed else 0
        worker_deficit = selected_stage.number_of_workers - number_of_workers if number_of_workers < selected_stage.number_of_workers else 0

        if volume_deficit > 0 and worker_deficit > 0:
            reason = 'both'
        elif volume_deficit > 0:
            reason = 'volume'
        elif worker_deficit > 0:
            reason = 'workers'
        else:
            reason = None

        if reason:
            Underperformance.objects.create(
                stage=selected_stage,
                reason=reason,
                deficit_volume=volume_deficit if reason in ['volume', 'both'] else None,
                deficit_workers=worker_deficit if reason in ['workers', 'both'] else None
            )

        # Отправляем сообщение пользователю о успешном сохранении данных
        bot.send_message(message.chat.id, f"Данные успешно внесены! Остаток объема: {remaining_volume:.1f} м²", reply_markup=get_work_keyboard())

    except ValueError:
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных.")
        bot.register_next_step_handler(message, get_completed_volume)
        return

@bot.message_handler(func=lambda message: message.text == "Гпp")
def gpr_menu(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    bot.send_message(message.chat.id, "Выберите отчет:", reply_markup=get_gpr_keyboard())

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back_to_work_menu(message):
    bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_work_keyboard())

@bot.message_handler(func=lambda message: message.text == "Сколько осталось")
def remaining_work(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    assigned_stages = model_user.assigned_stages.filter(completed=False).order_by('end_date')
    objects_with_stages = {stage.construction.object for stage in assigned_stages}

    if not assigned_stages.exists():
        bot.send_message(message.chat.id, "У вас нет незавершенных этапов.")
        return

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for obj in objects_with_stages:
        reply_markup.add(types.KeyboardButton(obj.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_object_for_remaining_work, objects_with_stages, assigned_stages)

def select_object_for_remaining_work(message, objects_with_stages, assigned_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_object = next(obj for obj in objects_with_stages if obj.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Объект не найден.")
        remaining_work(message)
        return

    constructions = {stage.construction for stage in assigned_stages if stage.construction.object == selected_object}

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for construction in constructions:
        reply_markup.add(types.KeyboardButton(construction.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_construction_for_remaining_work, selected_object, constructions, assigned_stages, objects_with_stages)

def select_construction_for_remaining_work(message, selected_object, constructions, assigned_stages, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_construction = next(constr for constr in constructions if constr.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Конструкция не найдена.")
        select_object_for_remaining_work(message, objects_with_stages, assigned_stages)
        return

    stages = [stage for stage in assigned_stages if stage.construction == selected_construction]

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, show_remaining_work, selected_object, stages, selected_construction, constructions, objects_with_stages)

def show_remaining_work(message, selected_object, stages, selected_construction, constructions, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_stage = next(stage for stage in stages if stage.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Этап не найден.")
        select_construction_for_remaining_work(message, selected_object, constructions, objects_with_stages)
        return

    remaining_volume = selected_stage.volume - sum(work.volume for work in selected_stage.completed_works.all())
    bot.send_message(message.chat.id, f"Оставшийся объем для этапа '{selected_stage.name}': {remaining_volume} м²", reply_markup=get_gpr_keyboard())

@bot.message_handler(func=lambda message: message.text == "Сколько выполнено")
def completed_work(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return
    
    assigned_stages = model_user.assigned_stages.filter(completed=False).order_by('end_date')
    objects_with_stages = {stage.construction.object for stage in assigned_stages}

    if not assigned_stages.exists():
        bot.send_message(message.chat.id, "У вас нет незавершенных этапов.")
        return

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for obj in objects_with_stages:
        reply_markup.add(types.KeyboardButton(obj.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_object_for_completed_work, objects_with_stages, assigned_stages)

def select_object_for_completed_work(message, objects_with_stages, assigned_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_object = next(obj for obj in objects_with_stages if obj.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Объект не найден.")
        completed_work(message)
        return

    constructions = {stage.construction for stage in assigned_stages if stage.construction.object == selected_object}

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for construction in constructions:
        reply_markup.add(types.KeyboardButton(construction.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_construction_for_completed_work, selected_object, constructions, assigned_stages, objects_with_stages)

def select_construction_for_completed_work(message, selected_object, constructions, assigned_stages, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_construction = next(constr for constr in constructions if constr.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Конструкция не найдена.")
        select_object_for_completed_work(message, objects_with_stages, assigned_stages)
        return

    stages = [stage for stage in assigned_stages if stage.construction == selected_construction]

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, show_completed_work, selected_object, stages, selected_construction, constructions, objects_with_stages)

def show_completed_work(message, selected_object, stages, selected_construction, constructions, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_stage = next(stage for stage in stages if stage.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Этап не найден.")
        select_construction_for_completed_work(message, selected_object, constructions, objects_with_stages)
        return

    total_completed_volume = sum(work.volume for work in selected_stage.completed_works.all())
    bot.send_message(message.chat.id, f"Объем выполненных работ для этапа '{selected_stage.name}': {total_completed_volume} м²", reply_markup=get_gpr_keyboard())

@bot.message_handler(func=lambda message: message.text == "Ежедневные отчеты")
def daily_reports(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return
    
    assigned_stages = model_user.assigned_stages.filter(completed=False).order_by('end_date')
    objects_with_stages = {stage.construction.object for stage in assigned_stages}

    if not assigned_stages.exists():
        bot.send_message(message.chat.id, "У вас нет незавершенных этапов.")
        return

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for obj in objects_with_stages:
        reply_markup.add(types.KeyboardButton(obj.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите объект:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_object_for_daily_reports, objects_with_stages, assigned_stages)

def select_object_for_daily_reports(message, objects_with_stages, assigned_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_object = next(obj for obj in objects_with_stages if obj.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Объект не найден.")
        daily_reports(message)
        return

    constructions = {stage.construction for stage in assigned_stages if stage.construction.object == selected_object}

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for construction in constructions:
        reply_markup.add(types.KeyboardButton(construction.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите конструкцию:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, select_construction_for_daily_reports, selected_object, constructions, assigned_stages, objects_with_stages)

def select_construction_for_daily_reports(message, selected_object, constructions, assigned_stages, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_construction = next(constr for constr in constructions if constr.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Конструкция не найдена.")
        select_object_for_daily_reports(message, objects_with_stages, assigned_stages)
        return

    stages = [stage for stage in assigned_stages if stage.construction == selected_construction]

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, show_daily_reports, selected_object, stages, selected_construction, constructions, objects_with_stages)

def show_daily_reports(message, selected_object, stages, selected_construction, constructions, objects_with_stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_gpr_keyboard())
        return

    try:
        selected_stage = next(stage for stage in stages if stage.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Этап не найден.")
        select_construction_for_daily_reports(message, selected_object, constructions, objects_with_stages)
        return

    daily_reports = selected_stage.daily_reports.all()
    if not daily_reports.exists():
        bot.send_message(message.chat.id, "Для этого этапа нет ежедневных отчетов.")
        return

    report_messages = "\n".join([f"{report.date.strftime('%d.%m.%Y')}: Выполнено: {report.completed_volume} м², Рабочих: {report.number_of_workers}" for report in daily_reports])
    bot.send_message(message.chat.id, f"Ежедневные отчеты для этапа '{selected_stage.name}':\n{report_messages}", reply_markup=get_gpr_keyboard())











# Директор
@bot.message_handler(func=lambda message: message.text == "Просрочки")
def director_overdue_stages(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id)
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Вы не зарегистрированы.")
        return

    if model_user.department != 'director':
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    underperforming_stages = Underperformance.objects.filter(
        stage__completed=False
    ).values('stage').distinct()

    stages = Stage.objects.filter(id__in=underperforming_stages)

    if not stages.exists():
        bot.send_message(message.chat.id, "Нет просроченных этапов.")
        return

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for stage in stages:
        reply_markup.add(types.KeyboardButton(stage.name))
    reply_markup.add(types.KeyboardButton("Назад"))

    bot.send_message(message.chat.id, "Выберите этап:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, show_stage_info, stages)

def show_stage_info(message, stages):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Вы вернулись назад.", reply_markup=get_director_keyboard())
        return

    try:
        selected_stage = next(stage for stage in stages if stage.name == message.text)
    except StopIteration:
        bot.send_message(message.chat.id, "Этап не найден.")
        director_overdue_stages(message)
        return

    underperformances = selected_stage.underperformances.all()
    reports = selected_stage.daily_reports.all()

    report_info = "\n".join([f"{report.date.strftime('%d.%m.%Y')}: Рабочих: {report.number_of_workers}, выполнено объема: {report.completed_volume} м²" for report in reports])
    underperformance_info = "\n".join([f"{up.date.strftime('%d.%m.%Y')}: Рабочих: {up.deficit_workers or '-'}, выполнено объема: {up.deficit_volume or '-'} м²" for up in underperformances])

    total_days = (selected_stage.end_date - selected_stage.start_date).days or 1
    daily_volume_needed = selected_stage.volume / total_days

    message_text = (
        f"<b>Объект:</b> {selected_stage.construction.object.name}\n"
        f"<b>Конструкция:</b> {selected_stage.construction.name}\n"
        f"<b>Этап:</b> {selected_stage.name}\n"
        f"<b>Ответственный:</b> {selected_stage.construction.object.responsible_person.get_name()}\n"
        f"<b>Количество рабочих:</b> {selected_stage.number_of_workers}\n"
        f"<b>Нужно выполнять в день:</b> {daily_volume_needed:.1f} м²\n"
        f"<b>Ежедневные отчеты:</b>\n{report_info}\n\n"
        f"<b>Просрочки:</b>\n{underperformance_info}"
    )

    bot.send_message(message.chat.id, message_text, parse_mode="HTML", reply_markup=get_director_keyboard())



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

