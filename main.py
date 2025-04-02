import argparse
import asyncio
import logging
from datetime import datetime

import aiofiles

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def listen_to_chat(host, port, file_path):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        logger.info("Установлено соединение")

        async with aiofiles.open(file_path, mode="ab") as log_file:
            while True:
                try:
                    message_bytes = await reader.readline()
                    if not message_bytes:
                        break

                    message_text = message_bytes.decode().rstrip()
                    logger.info(message_text)

                    timestamp = datetime.now().strftime("[%d.%m.%y %H:%M] ")
                    await log_file.write(timestamp.encode() + message_bytes)
                    await log_file.flush()

                except (ConnectionError, asyncio.IncompleteReadError) as e:
                    logger.error(f"Connection error: {e}")
                    break

    except asyncio.CancelledError:
        logger.debug("Chat parsing stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Клиент для подключения к чату",
    )
    parser.add_argument(
        "--host",
        default="minechat.dvmn.org",
        help="Хост сервера чата",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Порт сервера чата",
    )
    parser.add_argument(
        "--history",
        type=str,
        default="minechat.history",
        help="Путь к файлу для сохранения истории чата",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(listen_to_chat(args.host, args.port, args.history))
