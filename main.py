import asyncio
import json
import logging
from datetime import datetime

import aiofiles
from environs import Env

import gui
from exceptions import InvalidToken
from send_message import authorise, send_chat_message

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


async def send_msgs(
    host: str, port: int, account_hash: str, sending_queue: asyncio.Queue
):
    while True:
        message = await sending_queue.get()
        try:
            await send_chat_message(host, port, message, account_hash)
        except Exception as e:
            logger.error(f"Error when posting a message: {e}")


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


async def get_account_hash():
    try:
        async with aiofiles.open("token.json", "r") as file:
            user_token = json.loads(await file.read())
    except FileNotFoundError:
        logger.info("Authorization file not found! run `python3 register.py`")
        return

    return user_token.get("account_hash", None)


async def authorization(host, port, account_hash):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        try:
            logger.debug(await reader.readline())
            auth = await authorise(reader, writer, account_hash)
            logger.debug(await reader.readline())

            return auth

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")
        except InvalidToken as e:
            logger.error(f"Authorization error: {e}")
            raise

    except asyncio.CancelledError:
        logger.debug("Chat stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


async def main():
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("CHAT_PORT", 5000)
    post_port = env.int("POSTING_PORT", 5050)
    filepath = "minechat.history"
    account_hash = await get_account_hash()

    try:
        auth = await authorization(host, post_port, account_hash)
        if auth:
            logger.info(f"Authorization has been performed. User {auth.get("nickname")}")
    except InvalidToken:
        gui.show_message_box(
            "Invalid token", "Check the token. The server didn't recognize it"
        )
        return

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    await load_chat_history(filepath, messages_queue)
    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(host, port, messages_queue, history_queue),
        save_messages(filepath, history_queue),
        send_msgs(host, post_port, account_hash, sending_queue),
    )


if __name__ == "__main__":
    asyncio.run(main())
