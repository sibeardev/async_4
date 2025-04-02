# Чат-клиент для minechat

Асинхронный клиент для отправки и получения сообщений чата minechat

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/sibeardev/async_4.git
cd async_4
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

### Переменные окружения

Для удобства вы можете задать параметры подключения через переменные окружения:

```bash
export CHAT_HOST=[minechat_host]
export CHAT_PORT=5000  # Для чтения чата
export POSTING_PORT=5050  # Для отправки сообщений
```

## Использование

### Регистрация в чате

```bash
python register.py --username [USERNAME]
```

### Отправка сообщения

```bash
python send_message.py --message [MESSAGE_TEXT]
```

### Просмотр чата

```bash
python read_chat.py --history [FILE_HISTORY_PATH]
```

# Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).