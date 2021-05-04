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
PRAKTIKUM_AUTH_HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

STATUS_ERROR = 'Статус работы неизвестен. Сервер вернул значение: "{status}"'
STATUS_SUCCESS = 'У вас проверили работу "{homework}"!\n\n{status}'
STATUS_S = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
    'reviewing': 'Ваша работа прошла тесты и поступила на ревью.',
}
LOG_API_REQUEST = 'Отправка запроса к API.'
LOG_MSG_TO_TELEGRAM = 'Отправка сообщения в Telegram: "{message}".'
LOG_STARTUP = 'Бот запущен.'
LOG_EXCEPTION = 'Бот столкнулся с ошибкой: {exception}'
LOG_CONNECTION_FAILURE = ('Ошибка интернет соединения: {error}\n'
                          'URL: {url}\n'
                          'Заголовки: {headers}\n'
                          'Параметры: {params}\n')
LOG_SERVER_FAILURE = ('Ошибка - сбой сервера: {error}\n'
                      'URL: {url}\n'
                      'Заголовки: {headers}\n'
                      'Параметры: {params}\n')


bot = telegram.Bot(token=TELEGRAM_TOKEN)
logger = logging.getLogger(__name__)


def parse_homework_status(homework):
    status = homework['status']
    if status not in STATUS_S:
        raise ValueError(STATUS_ERROR.format(status=status))
    return STATUS_SUCCESS.format(
        homework=homework["homework_name"],
        status=STATUS_S[status],
    )


def get_homework_statuses(current_timestamp):
    logger.info(LOG_API_REQUEST)
    request_params = dict(
        url=PRAKTIKUM_API_URL,
        headers=PRAKTIKUM_AUTH_HEADERS,
        params={'from_date': current_timestamp},
    )
    try:
        homework_statuses = requests.get(**request_params)
    except ConnectionError as error:
        raise ConnectionError(
            LOG_CONNECTION_FAILURE.format(error=error, **request_params)
        )
    parsed_data = homework_statuses.json()
    for key in ('error', 'code'):
        if key in parsed_data:
            raise RuntimeError(
                LOG_SERVER_FAILURE.format(
                    error=parsed_data[key],
                    **request_params,
                )
            )
    return parsed_data


def send_message(message, bot_client=bot):
    logger.info(LOG_MSG_TO_TELEGRAM.format(message=message))
    return bot_client.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logger.debug(LOG_STARTUP)
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
            time.sleep(20 * 60)
        except Exception as exception:
            logger.exception(LOG_EXCEPTION.format(exception=exception))
            time.sleep(5 * 60)


if __name__ == '__main__':
    logging.basicConfig(
        filename=__file__ + '.log',
        filemode='a',
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    main()
