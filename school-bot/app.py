from flask import Flask, render_template, request, redirect, url_for
import json
import os
import threading
import time
import datetime
import random

app = Flask(__name__)

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ваш_токен')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6208544150'))

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

def get_current_day():
    day_num = datetime.datetime.now().weekday()
    return DAYS_OF_WEEK[day_num]

@app.route('/')
def index():
    schedule_data = load_schedule()
    dz = load_dz()
    
    # ДЗ на сегодня
    today = get_current_day()
    today_subjects = schedule_data.get(today, [])
    today_dz = []
    
    for subject in today_subjects:
        today_dz.append({
            'subject': subject,
            'hw': dz.get(subject),
            'emoji': SUBJECT_EMOJI.get(subject, "📝")
        })
    
    # Все ДЗ
    dz_list = []
    for subject, hw in dz.items():
        dz_list.append({
            'subject': subject,
            'hw': hw,
            'emoji': SUBJECT_EMOJI.get(subject, "📝")
        })
    
    # Статистика
    total_hw = len(dz)
    total_subjects = sum(len(subjects) for subjects in schedule_data.values())
    
    return render_template('index.html',
                         dz_list=dz_list,
                         today_dz=today_dz,
                         today=today,
                         day_emoji=DAY_EMOJI.get(today, "📅"),
                         total_hw=total_hw,
                         total_subjects=total_subjects,
                         subjects=SUBJECTS,
                         subject_emoji=SUBJECT_EMOJI,
                         days=DAYS_OF_WEEK)

@app.route('/add_hw', methods=['POST'])
def add_hw():
    subject = request.form.get('subject')
    hw = request.form.get('hw')
    
    if subject and hw:
        dz = load_dz()
        dz[subject] = hw
        save_data("data/dz.json", dz)
    
    return redirect(url_for('index'))

@app.route('/delete_hw/<subject>', methods=['POST'])
def delete_hw(subject):
    dz = load_dz()
    if subject in dz:
        del dz[subject]
        save_data("data/dz.json", dz)
    return redirect(url_for('index'))

@app.route('/clear_all', methods=['POST'])
def clear_all():
    save_data("data/dz.json", {})
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
