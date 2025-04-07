import asyncio
import logging
from datetime import datetime

import aiofiles
from environs import Env

import gui

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def read_msgs(
    host: str, port: int, messages_queue: asyncio.Queue, history_queue: asyncio.Queue
):
    try:
        reader, writer = await asyncio.open_connection(host, port)

        while True:
            try:
                message_bytes = await reader.readline()
                if not message_bytes:
                    break

                message_text = message_bytes.decode().rstrip()
                timestamp = datetime.now().strftime("[%d.%m.%y %H:%M] ")
                message = f"{timestamp}{message_text}"
                messages_queue.put_nowait(message)
                history_queue.put_nowait(message)

            except (ConnectionError, asyncio.IncompleteReadError) as e:
                logger.error(f"Connection error: {e}")
                break

    except asyncio.CancelledError:
        logger.debug("Chat parsing stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


async def save_messages(filepath: str, queue: asyncio.Queue):
    async with aiofiles.open(filepath, mode="a", encoding="utf-8") as history_file:
        while True:
            message = await queue.get()
            try:
                await history_file.write(f"{message}\n")
                await history_file.flush()
            except Exception as e:
                logger.error(f"Error when saving a message: {e}")


async def load_chat_history(filepath: str, queue: asyncio.Queue):
    try:
        async with aiofiles.open(filepath, mode="r", encoding="utf-8") as history_file:
            async for line in history_file:
                cleaned_line = line.strip()
                if cleaned_line:
                    await queue.put(cleaned_line)
    except FileNotFoundError:
        logger.warning(f"History file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error when loading history: {str(e)}")


async def main():
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("CHAT_PORT", 5000)
    filepath = "minechat.history"

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    await load_chat_history(filepath, messages_queue)
    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(host, port, messages_queue, history_queue),
        save_messages(filepath, history_queue),
    )


if __name__ == "__main__":
    asyncio.run(main())
