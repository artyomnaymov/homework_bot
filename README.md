## **_Telegram-bot homework status Yandex.Practicum_**

![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg?style=plastic)
![python-telegram-bot 13.7](https://img.shields.io/badge/python--telegram--bot-13.7-green?style=plastic)

---

### Описание

Telegram-bot для проверки статуса домашней работы в Яндекс.Практикум.

Бота обращаться к API сервиса Практикум.Домашка, узнает статус вашей домашней работы: взята ли ваша домашка в ревью,
проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

---

### Установка

#### Для локального запуска проекта

1. Создайте виртуальное окружение в директории проекта `python -m venv /venv`
2. Активировать виртуальное окружение `source venv/scripts/activate`
3. Установить зависимости `pip install -r requirement.txt`
4. Запустить файл `homework.py`

#### Для запуска проекта на heroku

1. Зарегистрируйтесь на [Heroku](https://www.heroku.com)
2. Создайте приложение (кнопка _New_ → _Create new app_)
3. Свяжите ваш аккаунт Heroku c GitHub:
    - в интерфейсе Heroku зайдите в раздел Deploy,
    - в разделе Deployment method выберите GitHub и нажмите на кнопку Connect to GitHub.
4. Добавьте переменные окружения в heroku:
    - Перейдите в настройки Heroku, в разделе _Settings_ → _Config Vars_.
    - Нажмите _Reveal Config Vars_ и добавьте ключ и значение для каждой переменной:
        - `PRACTICUM_TOKEN`,
        - `TELEGRAM_TOKEN`,
        - `TELEGRAM_CHAT_ID`.
5. Запустите бота:
    - Перейдите во вкладку Resources
    - Активируйте свич напротив строки worker python homework.py.
