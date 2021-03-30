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
PRAKTIKUM_AUTH_HEADER = f'OAuth {PRAKTIKUM_TOKEN}'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

VERDICT_REJECTED = 'К сожалению в работе нашлись ошибки.'
VERDICT_APPROVED = ('Ревьюеру всё понравилось, '
                    'можно приступать к следующему уроку.')
VERDICT_REVIEWING = 'Ваша работа прошла тесты и поступила на ревью.'
VERDICT_ERROR = 'Статус работы неизвестен. Сервер вернул значение: "{verdict}"'
VERDICT_SUCCESS = 'У вас проверили работу "{homework}"!\n\n{verdict}'
VERDICT_DICT = {
    'rejected': VERDICT_REJECTED,
    'approved': VERDICT_APPROVED,
    'reviewing': VERDICT_REVIEWING,
}
LOG_API_REQUEST = 'Отправка запроса к API.'
LOG_MSG_TO_TELEGRAM = 'Отправка сообщения в Telegram: "{message}".'
LOG_STARTUP = '{bot_name} запущен.'
LOG_EXCEPTION = 'Бот столкнулся с ошибкой: {exception}'


def parse_homework_status(homework):
    if homework['status'] not in VERDICT_DICT:
        raise KeyError(VERDICT_ERROR.format(verdict=homework['status']))
    verdict = VERDICT_DICT[homework['status']]
    return VERDICT_SUCCESS.format(
            homework=homework["homework_name"],
            verdict=verdict,
    )


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'{PRAKTIKUM_AUTH_HEADER}'}
    params = {'from_date': current_timestamp}
    logging.info(f'{LOG_API_REQUEST}')
    homework_statuses = requests.get(
        PRAKTIKUM_API_URL,
        headers=headers,
        params=params,
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.error(LOG_MSG_TO_TELEGRAM.format(message=message))
    return bot_client.send_message(CHAT_ID, message)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s"
    )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug(LOG_STARTUP.format(bot_name=bot.name))
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

        except Exception:
            logging.error(LOG_EXCEPTION.format(exception=Exception))
            time.sleep(5)


if __name__ == '__main__':
    main()
