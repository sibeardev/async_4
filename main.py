import asyncio
import logging
from datetime import datetime

import aiofiles

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def listen_to_chat():
    try:
        reader, writer = await asyncio.open_connection("minechat.dvmn.org", 5000)
        logger.info("Установлено соединение")

        async with aiofiles.open("chat_log.txt", mode="ab") as log_file:
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

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


if __name__ == "__main__":
    asyncio.run(listen_to_chat())
