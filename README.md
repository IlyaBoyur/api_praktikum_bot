# Telegram Bot for Homework updates
* This bot requests Yandex.Praktikum REST API for homework updates every 20 minutes.
* In case of an error exception is logged into a file homework.py.log

## Technologies
* Python 3.7.2
* Deployed with [Heroku](https://www.heroku.com/)
* for packages see requirements.txt in root folder


## How to use bot
1. Create .env text file in a root directory with the following content:
```bash
PRAKTIKUM_TOKEN=<practikum token value>
TELEGRAM_CHAT_ID=<your own telegram chat ID>
TELEGRAM_TOKEN=<telegram bot token>
```

2. Start bot:
```bash
python3 homework.py
```

## Authors
[Ilya Boyur](https://github.com/IlyaBoyur)
