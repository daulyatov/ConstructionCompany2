import logging
import telebot
from telebot import types
from django.conf import settings
import datetime
from django.utils import timezone
from .models import Object, Construction, Stage, TelegramUser
from .keyboards import get_back_keyboard, get_contract_keyboard, get_distribution_keyboard, get_objects_keyboard, \
            get_constructions_keyboard, get_work_keyboard, get_objects_keyboard_for_distribution, get_stages_keyboard, get_confirmation_keyboard, get_workers_keyboard, get_objects_keyboard_with_back

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

    bot.send_message(message.chat.id, "Выберите свой отдел:", reply_markup=keyboard)
    bot.register_next_step_handler(message, save_department)

def save_department(message):
    department_map = {
        "Договорной отдел": "contract",
        "Отдел распределения": "distribution",
        "Рабочий отдел": "work"
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
    else:
        return types.ReplyKeyboardMarkup(resize_keyboard=True)

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


user_sessions = {}


@bot.message_handler(func=lambda message: message.text.lower() == "назначить рабочего")
def assign_worker(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
    user_sessions[message.chat.id] = {'selected_workers': []}

    # Теперь выбираем объекты, назначенные конкретному пользователю
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
        if selected_stage.workers_assigned.exists():
            assigned_workers = selected_stage.workers_assigned.all()
            worker_names = ", ".join([worker.get_name() for worker in assigned_workers])
            deadline = selected_stage.deadline.strftime("%d.%m.%Y") if selected_stage.deadline else "не установлена"
            bot.send_message(message.chat.id, f"На этапе уже назначены рабочие: {worker_names}. Срок выполнения: {deadline}. Хотите перезаписать?", reply_markup=get_confirmation_keyboard())
            bot.register_next_step_handler(message, confirm_overwrite_assignment)
        else:
            bot.send_message(message.chat.id, "Выберите рабочих для назначения на этап. После выбора нажмите 'Подтвердить':", reply_markup=get_workers_keyboard([]))
            bot.register_next_step_handler(message, select_workers_for_stage, selected_stage)
    except Stage.DoesNotExist:
        bot.send_message(message.chat.id, "Этап не найден. Введите корректное название этапа или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_stage_for_worker_assignment, selected_construction)

def confirm_overwrite_assignment(message):
    if message.text.lower() == "да":
        bot.send_message(message.chat.id, "Выберите рабочих для назначения на этап. После выбора нажмите 'Подтвердить':", reply_markup=get_workers_keyboard([]))
        bot.register_next_step_handler(message, select_workers_for_stage, user_sessions[message.chat.id]['selected_stage'])
    elif message.text.lower() == "нет":
        bot.send_message(message.chat.id, "Выберите этап:", reply_markup=get_stages_keyboard(user_sessions[message.chat.id]['selected_construction']))
        bot.register_next_step_handler(message, select_stage_for_worker_assignment, user_sessions[message.chat.id]['selected_construction'])
    else:
        bot.send_message(message.chat.id, "Неверный ввод. Пожалуйста, выберите 'Да' или 'Нет'.", reply_markup=get_confirmation_keyboard())
        bot.register_next_step_handler(message, confirm_overwrite_assignment)

def select_workers_for_stage(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    if message.text.lower() == "подтвердить":
        selected_workers = user_sessions[message.chat.id]['selected_workers']
        if not selected_workers:
            bot.send_message(message.chat.id, "Вы не выбрали ни одного рабочего. Пожалуйста, выберите рабочих и нажмите 'Подтвердить'.", reply_markup=get_workers_keyboard(selected_workers))
            bot.register_next_step_handler(message, select_workers_for_stage, selected_stage)
        else:
            bot.send_message(message.chat.id, "Введите срок выполнения этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, save_workers_and_deadline, selected_stage)
        return

    worker_name = message.text
    try:
        worker = TelegramUser.objects.get(first_name=worker_name, department='work')
        user_sessions[message.chat.id]['selected_workers'].append(worker)
        bot.send_message(message.chat.id, f"Рабочий {worker.get_name()} добавлен. Выберите следующего рабочего или нажмите 'Подтвердить'.", reply_markup=get_workers_keyboard(user_sessions[message.chat.id]['selected_workers']))
        bot.register_next_step_handler(message, select_workers_for_stage, selected_stage)
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Рабочий не найден. Попробуйте снова или нажмите 'назад'.", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, select_workers_for_stage, selected_stage)

def save_workers_and_deadline(message, selected_stage):
    if message.text.lower() == "назад":
        bot.send_message(message.chat.id, "Назначение рабочего отменено.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
        return

    try:
        deadline = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        current_date = datetime.datetime.now()

        if deadline < current_date:
            bot.send_message(message.chat.id, "Нельзя назначить прошедшую дату. Введите срок выполнения этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(message, save_workers_and_deadline, selected_stage)
            return

        selected_workers = user_sessions[message.chat.id]['selected_workers']
        selected_stage.workers_assigned.clear()  # Очистка предыдущих назначений
        for worker in selected_workers:
            selected_stage.workers_assigned.add(worker)
        
        selected_stage.deadline = deadline  # Сохранение даты завершения
        selected_stage.save()
        
        worker_names = ", ".join([worker.get_name() for worker in selected_workers])
        formatted_deadline = deadline.strftime("%d.%m.%Y")
        bot.send_message(message.chat.id, f"Рабочие {worker_names} успешно назначены на этап '{selected_stage.name}' до {formatted_deadline}.", reply_markup=get_distribution_keyboard())
        user_sessions.pop(message.chat.id, None)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты. Введите срок выполнения этапа в формате 'дд.мм.гггг':", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(message, save_workers_and_deadline, selected_stage)

@bot.message_handler(func=lambda message: message.text.lower() == "список назначений")
def show_assignments_list(message):
    user = TelegramUser.objects.get(user_id=message.from_user.id)
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
                        worker_count = stage.workers_assigned.count()
                        deadline = stage.deadline.strftime("%d.%m.%Y") if stage.deadline else "не установлена"
                        assignments_message += f"    - <b>Этап: {stage.name}</b> (Рабочих: {worker_count}, Срок выполнения: {deadline})\n"
                else:
                    assignments_message += "    - <b>Нет этапов.</b>\n"
        else:
            assignments_message += "  <b>Нет конструкций.</b>\n"
        assignments_message += "\n"

    bot.send_message(message.chat.id, assignments_message, parse_mode="HTML", reply_markup=get_distribution_keyboard())




# Обработчик для кнопки "Начать работу"
@bot.message_handler(func=lambda message: message.text == "Начать работу")
def start_work(message):
    user = message.from_user
    try:
        model_user = TelegramUser.objects.get(user_id=user.id, department='work')
    except TelegramUser.DoesNotExist:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в рабочем отделе.")
        return
    
    # Получаем этапы, назначенные пользователю, отсортированные по дате
    assigned_stages = model_user.assigned_stages.filter(deadline__isnull=False).order_by('deadline')

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
        bot.send_message(message.chat.id, "Выберите этап:", reply_markup=start_work(message))
        return

    construction = stage.construction
    object = construction.object
    deadline = stage.deadline

    # Расчет оставшегося времени
    today = timezone.now().date()
    delta = deadline - today
    months_left = delta.days // 30
    days_left = delta.days % 30

    # Формирование сообщения
    report_message = (
        f"<b>Объект:</b> {object.name}\n"
        f"<b>Конструкция:</b> {construction.name}\n"
        f"<b>Этап:</b> {stage.name} (объем: {stage.volume} м²)\n"
        f"<b>Срок выполнения:</b> {deadline.strftime('%d.%m.%Y')}\n"
        f"<b>Осталось:</b> {months_left} месяцев и {days_left} дней\n"
        f"<b>Назначенные рабочие:</b> {', '.join([worker.get_name() for worker in stage.workers_assigned.all()])}\n"
    )

    # Отправка сообщения пользователю
    bot.send_message(message.chat.id, report_message, parse_mode="HTML", reply_markup=get_work_keyboard())


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

