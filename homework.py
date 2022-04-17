import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ResponseError, SendMessageError

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

# Устанавливаем настройки logger для текущего файла
logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого будут логироваться события
logger.setLevel(logging.DEBUG)
# Указываем обработчик логов
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
# Создаем форматер
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# Применяем форматер к хендлеру
handler.setFormatter(formatter)


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат, определяемый переменной окружения.
    :param bot: Экземпляр класса Bot
    :param message: Строка с текстом сообщения
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение: "{message}", успешно отправлено в чат')
    except SendMessageError as error:
        logger.error(f'Ошибка при отправлении сообщения: "{error}"')


def get_api_answer(current_timestamp):
    """
    Делает запрос к API-сервиса.
    В случае успешного запроса возвращается ответ API.
    :param current_timestamp: Временная метка
    """
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    error_msg = 'При обращении к адресу "{}" вернулась ошибка: "{}"'
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except ResponseError(error_msg.format(ENDPOINT, response.status_code)):
        logger.error(error_msg.format(ENDPOINT, response.status_code))
    if response.status_code != HTTPStatus.OK:
        logger.error(error_msg.format(ENDPOINT, response.status_code))
        raise ResponseError(error_msg.format(ENDPOINT, response.status_code))
    logger.debug(f"Ответ API успешно получен {response.json()}")
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на корректность.
    Если ответ API соответствует ожиданиям, то возвращается список домашних
    работ, доступный в ответе API по ключу 'homeworks'.
    :param response: ответ API
    """
    if not isinstance(response, dict):
        error_msg = 'В ответе API вместо словаря "homeworks" вернулся {}'
        response_type = type(response)
        logger.error(error_msg.format(response_type))
        raise TypeError(error_msg.format(response_type))
    if not response:
        error_msg = "В ответе API вернулся пустой словарь"
        logger.error(error_msg)
        raise ValueError(error_msg)
    if "homeworks" not in response:
        error_msg = 'В ответе API отсутствует ключ "homeworks"'
        logger.error(error_msg)
        raise ValueError(error_msg)

    homeworks = response.get("homeworks")

    if not isinstance(homeworks, list):
        error_msg = 'В ответе API, в ключе "homeworks" вместо списка ' "приходит {}"
        logger.error(error_msg.format(type(homeworks)))
        raise TypeError(error_msg.format(type(homeworks)))
    logger.debug("Ответ API успешно проверен")
    return homeworks


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В случае успеха, функция возвращает подготовленную для отправки в Telegram
    строку, содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    :param homework: один элемент из списка домашних работ
    """
    error_msg = 'В ответе API отсутствует ключ "{}"'
    if not isinstance(homework, dict):
        error_msg = 'В ответе API вместо словаря "homework" вернулся {}'
        homework_type = type(homework)
        logger.error(error_msg.format(homework_type))
        raise TypeError(error_msg.format(homework_type))
    if "homework_name" not in homework:
        logger.error(error_msg.format("homework_name"))
        raise KeyError('В ответе API отсутствует ключ "homework_name"')
    if "status" not in homework:
        logger.error(error_msg.format("status"))
        raise KeyError(error_msg.format("status"))
    if homework.get("status") not in HOMEWORK_STATUSES.keys():
        error_msg = "В ответе API обнаружен недокументированный статус: {}"
        logger.error(error_msg.format(homework.get("status")))
        raise KeyError(error_msg.format(homework.get("status")))
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    verdict = HOMEWORK_STATUSES.get(homework_status)
    logger.debug("Статус домашней работы успешно извлечен")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Проверяет доступность переменных окружения, необходимых для работы программы.
    Если отсутствует хотя бы одна переменная окружения — функция
    возвращает False, иначе — True.
    """
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logger.debug("Проверка переменных окружения завершилась успешно")
        return True
    logger.critical(
        "Отсутствует одна или несколько обязательных " "переменных окружения"
    )
    return False


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        return

    # создаем экземпляр класса бота
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    # создаем переменную содержащую текущий таймпстемп
    current_timestamp = int(time.time())
    # создаем переменные для кэша
    cache = dict()
    cache_error = dict()

    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                logger.debug("В ответе API есть домашняя работа")
                homework = homeworks[0]
                homework_id = homework.get("id")
                cached_homework = cache.get(homework_id)
                if cached_homework:
                    if cached_homework.get("status") != homework.get("status"):
                        message = parse_status(homework=homework)
                        send_message(bot=bot, message=message)
                        cache[homework_id] = homework
                else:
                    message = parse_status(homework=homework)
                    send_message(bot=bot, message=message)
                    cache[homework_id] = homework
        except Exception as error:
            message = f"Сбой в работе программы: {error.args}"
            cached_error = cache_error.get("error")
            if cached_error:
                if cached_error.get("error") != error.args:
                    send_message(bot=bot, message=message)
                    cache_error["error"] = error.args
            else:
                send_message(bot=bot, message=message)
                cache_error["error"] = error.args
        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
