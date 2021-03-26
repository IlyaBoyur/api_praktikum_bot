import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
PRAKTIKUM_API_URL = ('https://praktikum.yandex.ru/api/'
                     'user_api/homework_statuses/')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework['status'] == 'approved':
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    else:
        verdict = 'Ваша работа прошла тесты и поступила на ревью.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    logging.info('Отправка запроса к API.')
    homework_statuses = requests.get(
        PRAKTIKUM_API_URL,
        headers=headers,
        params=params,
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.error(f'Отправка сообщения в Telegram: "{message}".')
    return bot_client.send_message(CHAT_ID, message)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s"
    )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    logging.debug(f'{bot.first_name} запущен.')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            # Update timestamp
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp,
            )
            # Ask every 20 minutes
            time.sleep(1200)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
