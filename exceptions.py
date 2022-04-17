class SendMessageError(Exception):
    """Вызывается при ошибке отправки сообщения"""

    pass


class ResponseError(Exception):
    """Вызывается при ошибке получения ответа API"""

    pass
