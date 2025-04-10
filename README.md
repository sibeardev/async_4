# Чат-клиент для minechat

Асинхронный GUI клиент для отправки и получения сообщений чата minechat

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

### Запуск чата

```bash
python main.py [-h] [--host HOST] [--read_port READ_PORT] [--post_port POST_PORT] [--history HISTORY]
```

```
--host (по умолчанию: minechat.dvmn.org) — адрес сервера.
--read_port (по умолчанию: 5000) — порт для чтения сообщений.
--post_port (по умолчанию: 5050) — порт для отправки сообщений.
--history (необязательный) — путь к файлу для сохранения истории чата.
```
# Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
