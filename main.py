import asyncio
import logging

from environs import Env

import gui

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def read_msgs(host: str, port: int, queue: asyncio.Queue):
    try:
        reader, writer = await asyncio.open_connection(host, port)

        while True:
            try:
                message_bytes = await reader.readline()
                if not message_bytes:
                    break

                message_text = message_bytes.decode().rstrip()
                queue.put_nowait(message_text)

            except (ConnectionError, asyncio.IncompleteReadError) as e:
                logger.error(f"Connection error: {e}")
                break

    except asyncio.CancelledError:
        logger.debug("Chat parsing stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


async def main():
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("CHAT_PORT", 5000)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(host, port, messages_queue),
    )


if __name__ == "__main__":
    asyncio.run(main())
