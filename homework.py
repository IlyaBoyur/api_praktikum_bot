import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import HTTPError


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
LOG_EXCEPTION_STATUS = ('Статус ответа сервера Я.Практикума'
                        'отличен от 200: {exception}')
LOG_EXCEPTION_FORMAT = ('Сервер вернул нелжиданный формат данных.'
                        'Описание ошибки: {exception}')
STATUS_OK = 200


bot = telegram.Bot(token=TELEGRAM_TOKEN)
logger = logging.getLogger(__name__)


def setup_logger(logger, filename):
    handler = logging.FileHandler(filename, mode='a')
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


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
    logger.info(f'{LOG_API_REQUEST}')
    homework_statuses = requests.get(
        PRAKTIKUM_API_URL,
        headers=headers,
        params=params,
    )
    if homework_statuses.status_code != STATUS_OK:
        raise HTTPError(LOG_EXCEPTION_STATUS.format(exception=str(HTTPError)))
    parsed_data = homework_statuses.json()
    erroneous_format = parsed_data.get('error') or parsed_data.get('code')
    if erroneous_format:
        raise requests.exceptions.ContentDecodingError(
            LOG_EXCEPTION_FORMAT.format(exception=erroneous_format)
        )
    return parsed_data


def send_message(message):
    logger.error(LOG_MSG_TO_TELEGRAM.format(message=message))
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logger.debug(LOG_STARTUP.format(bot_name=bot.name))
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )
            # Update timestamp
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp,
            )
            # Ask every 20 minutes
            time.sleep(1200)

        except Exception:
            logger.exception(LOG_EXCEPTION.format(exception=str(Exception)))
            time.sleep(5)


if __name__ == '__main__':
    setup_logger(logger, 'data.log')
    main()
