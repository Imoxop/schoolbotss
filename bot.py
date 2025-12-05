import telebot
from telebot import types
import json
import os
import time
import datetime
import schedule
import random
import threading

# Настройки из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ваш_токен')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6208544150'))

bot = telebot.TeleBot(BOT_TOKEN)

# Словари для красивых сообщений
SUBJECT_EMOJI = {
    "математика": "🔢", "русский": "📖", "литература": "📚", "алгебра": "🧮", "геометрия": "📐",
    "физика": "⚡", "биология": "🔬", "география": "🌍", "информатика": "💻", "химия": "🧪",
    "история": "🏛️", "обществознание": "👥", "английский": "🇬🇧", "физкультура": "🏃", "ОБЖ": "⚠️",
}

DAY_EMOJI = {
    "Понедельник": "🌕", "Вторник": "🌖", "Среда": "🌗", "Четверг": "🌘", 
    "Пятница": "🌑", "Суббота": "🌒", "Воскресенье": "🌓"
}

DAYS_OF_WEEK = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
DAYS_OF_WEEK_RU = {i: day for i, day in enumerate(DAYS_OF_WEEK)}
SUBJECTS = list(SUBJECT_EMOJI.keys())

# Функции для работы с данными
def load_data(filename, default_data=None):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка загрузки {filename}: {e}")
    return default_data if default_data is not None else {}

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"Ошибка сохранения {filename}: {e}")
        return False

def load_dz():
    return load_data("data/dz.json", {})

def load_schedule():
    default_schedule = {day: [] for day in DAYS_OF_WEEK}
    return load_data("data/schedule.json", default_schedule)

def load_groups():
    return load_data("data/groups.json", {})

def save_group(chat_id, chat_title, chat_type):
    groups = load_groups()
    groups[str(chat_id)] = {
        "title": chat_title,
        "type": chat_type,
        "added": time.time(),
        "active": True,
        "auto_send": True,
        "send_time": "08:00"
    }
    return save_data("data/groups.json", groups)

# Клавиатуры
def main_keyboard(user_id=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        "➕ Добавить ДЗ", "📚 Показать ДЗ",
        "📅 Расписание", "📖 ДЗ на сегодня",
        "🎲 Случайный мем", "⭐ Мотивация"
    ]
    
    if user_id == ADMIN_ID:
        buttons.append("👑 Админ")
    
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        kb.row(*[types.KeyboardButton(btn) for btn in row])
    
    return kb

# Команды бота
@bot.message_handler(commands=['start', 'help'])
def start(message):
    welcome = """
👋 *Привет! Я бот для домашних заданий!*

✨ *Что я умею:*
• 📝 Сохранять домашние задания
• 📅 Показывать расписание
• 🔔 Отправлять ДЗ в группы
• 🎲 Радовать мемами
• 💪 Мотивировать на учёбу

🚀 *Используй кнопки ниже!*
    """
    
    bot.send_message(
        message.chat.id,
        welcome,
        parse_mode="Markdown",
        reply_markup=main_keyboard(message.from_user.id)
    )

@bot.message_handler(commands=['today'])
def today_command(message):
    day = DAYS_OF_WEEK_RU.get(datetime.datetime.now().weekday(), "Понедельник")
    schedule_data = load_schedule()
    dz = load_dz()
    
    response = f"{DAY_EMOJI.get(day, '📅')} *ДЗ на {day}:*\n\n"
    
    subjects = schedule_data.get(day, [])
    if not subjects:
        response += "🎉 На сегодня уроков нет!\n✨ Отличный день для отдыха!"
    else:
        hw_count = 0
        for subject in subjects:
            if subject in dz:
                hw_count += 1
                emoji = SUBJECT_EMOJI.get(subject, "📝")
                response += f"{emoji} *{subject}:*\n{dz[subject]}\n\n"
        
        if hw_count == 0:
            response += "🎉 На сегодня заданий нет!\n✨ Можно заняться чем-то интересным!"
        else:
            response += f"📊 *Всего заданий:* {hw_count}"
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(content_types=['new_chat_members'])
def new_chat_members(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            chat_id = message.chat.id
            chat_title = message.chat.title
            chat_type = message.chat.type
            
            save_group(chat_id, chat_title, chat_type)
            
            welcome_text = f"""
🤖 *Я присоединился к группе {chat_title}!*

📌 *Команды в группе:*
/today - ДЗ на сегодня
/week - Расписание
/dz - Все задания
/meme - Случайный мем

⏰ *Автоотправка:* 08:00 каждый день
            """
            
            bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

# Запуск планировщика для автоотправки
def send_daily_homework():
    groups = load_groups()
    
    if not groups:
        return
    
    day = DAYS_OF_WEEK_RU.get(datetime.datetime.now().weekday(), "Понедельник")
    schedule_data = load_schedule()
    dz = load_dz()
    
    subjects = schedule_data.get(day, [])
    if not subjects:
        return
    
    response = f"{DAY_EMOJI.get(day, '📅')} *ДЗ на {day}:*\n\n"
    
    hw_found = False
    for subject in subjects:
        if subject in dz:
            hw_found = True
            emoji = SUBJECT_EMOJI.get(subject, "📝")
            response += f"{emoji} *{subject}:*\n{dz[subject]}\n\n"
    
    if not hw_found:
        response = f"{DAY_EMOJI.get(day, '📅')} *{day}*\n\n🎉 На сегодня заданий нет!\n✨ Хорошего дня!"
    
    for chat_id, group_info in groups.items():
        if group_info.get('active', True) and group_info.get('auto_send', True):
            try:
                bot.send_message(int(chat_id), response, parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки в группу {chat_id}: {e}")

def schedule_job():
    """Запуск планировщика"""
    schedule.every().day.at("08:00").do(send_daily_homework)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("🤖 Бот запущен на Railway!")
    
    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_job, daemon=True)
    scheduler_thread.start()
    
    # Запускаем бота
    bot.polling(none_stop=True, interval=1, timeout=30)