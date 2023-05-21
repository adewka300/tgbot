import telebot
import requests
import datetime
import re

bot_token = '6238775661:AAECeQtMJjFtnDAH_ZL3ylVPjbka0YXGRAQ'

bot = telebot.TeleBot(bot_token)

user_groups = {}

def getInfoSubj(sbj, day, num, date):
    sublst = dict.fromkeys(['obj', 'teacher', 'room'])
    length = len(sbj.get(day).get(num))
    for i in range(length):
        if (sbj.get(day).get(num)[i].get('dt') >= date) and (sbj.get(day).get(num)[i].get('df') <= date):
            sublst['obj'] = sbj.get(day).get(num)[i].get('sbj') + " ("+sbj.get(day).get(num)[i].get('type')+")"
            sublst['teacher'] = sbj.get(day).get(num)[i].get('teacher')
            sublst['room'] = ', '.join(sbj.get(day).get(num)[i].get('shortRooms') )
    return sublst

def get_schedule(group, day):
    cookies = {
        '_ym_uid': '1680981569370612538',
        '_ym_d': '1680981569',
        'group': group,
        '_ym_isad': '2',
        '_ym_visorc': 'w',
    }

    headers = {
        'authority': 'rasp.dmami.ru',
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'referer': 'https://rasp.dmami.ru/',
        'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'group': group,
        'session': '0',
    }

    date = str(datetime.datetime.now())

    times = {
        1: '9:00-10:30',
        2: '10:40-12:10',
        3: '12:20-13:50',
        4: '14:30-16:00',
        5: '16:10-17:40',
        6: '17:50-19:20',
        7: '19:30-21:00',
    }

    response = requests.get('https://rasp.dmami.ru/site/group', params=params, cookies=cookies, headers=headers).json().get('grid')

    schedule = []
    day = str(day)
    day_schedule = []
    for j in range(1, 8):
        num = str(j)
        if getInfoSubj(response, day, num, date).get('obj') != None:
            subject = getInfoSubj(response, day, num, date)
            if subject['teacher'] != '':
                subject_info = f"{subject['obj']}\n{subject['teacher']}\n{subject['room']}"
            else:
                subject_info = f"{subject['obj']}\n{subject['room']}"
            day_schedule.append(f"{times[j]}: {subject_info}\n")
    if len(day_schedule) != 0:
        schedule.append(day_schedule)
    return schedule


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    user_groups.pop(user_id, None)
    bot.reply_to(message, "Привет :)\nЯ бот, который умеет отправлять расписание студентов Московского Политеха.\nВведи номер своей группы и я скину твое расписание!")

@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.chat.id
    user_groups.pop(user_id, None)
    markup = telebot.types.ReplyKeyboardRemove()
    bot.reply_to(message, "Бот остановлен.", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "Введи номер группы, чтобы получить расписание!\nЧтобы изменить номер группы, выбери /changegroup в меню")

@bot.message_handler(commands=['changegroup'])
def changegroup_command(message):
    user_id = message.chat.id
    bot.reply_to(message, "Введи номер другой группы:")
    bot.register_next_step_handler(message, process_group_change, user_id)

def process_group_change(message, user_id):
    group = message.text

    if not re.match(r'^\d{3}-\d{3}$', group):
        bot.send_message(user_id, "Введи корректный номер группы в формате XXX-XXX.")
        return

    user_groups[user_id] = group

    bot.send_message(user_id, "Номер группы успешно изменен!")

@bot.message_handler(func=lambda message: True)
def schedule_command(message):
    user_id = message.chat.id

    if user_id not in user_groups:
        group = message.text

        if not re.match(r'^\d{3}-\d{3}$', group):
            bot.reply_to(message, "Введи корректный номер группы в формате XXX-XXX.")
            return

        user_groups[user_id] = group

        markup = telebot.types.ReplyKeyboardMarkup(row_width=3)
        markup.add(*[telebot.types.KeyboardButton(day) for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']])
        bot.reply_to(message, "Выбери день недели:", reply_markup=markup)
    else:
        group = user_groups[user_id]
        day = message.text

        day_mapping = {
            'Понедельник': 1,
            'Вторник': 2,
            'Среда': 3,
            'Четверг': 4,
            'Пятница': 5,
            'Суббота': 6
        }
        day_number = day_mapping.get(day)

        if not day_number:
            bot.reply_to(message, "Введи корректный день недели.")
            return

        schedule = get_schedule(group, day_number)

        if schedule:
            for day_schedule in schedule:
                bot.send_message(message.chat.id, "\n".join(day_schedule))
        else:
            bot.reply_to(message, "В выбранный день нет занятий.")

bot.polling()
