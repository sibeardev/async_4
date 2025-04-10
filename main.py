import asyncio
import json
import logging
from datetime import datetime

import aiofiles
import anyio
from environs import Env

import gui
from exceptions import InvalidToken
from send_message import authorise, send_chat_message

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

watchdog_logger = logging.getLogger("watchdog")
watchdog_logger.propagate = False
watchdog_handler = logging.StreamHandler()
watchdog_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
watchdog_logger.addHandler(watchdog_handler)


async def read_msgs(
    host: str,
    port: int,
    messages_queue: asyncio.Queue,
    history_queue: asyncio.Queue,
    status_updates_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
):
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    try:
        reader, writer = await asyncio.open_connection(host, port)
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
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
                watchdog_queue.put_nowait("New message in chat")
            except (ConnectionError, asyncio.IncompleteReadError) as e:
                logger.error(f"Connection error: {e}")
                break

    except asyncio.CancelledError:
        logger.debug("Chat parsing stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)


async def send_msgs(
    host: str,
    port: int,
    account_hash: str,
    sending_queue: asyncio.Queue,
    status_updates_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
):
    while True:
        message = await sending_queue.get()
        try:
            await send_chat_message(
                host, port, message, account_hash, status_updates_queue
            )
            watchdog_queue.put_nowait("Message sent")
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


async def watch_for_connection(watchdog_queue: asyncio.Queue, timeout: int = 10):
    while True:
        try:
            async with asyncio.timeout(timeout):
                message = await watchdog_queue.get()
                watchdog_logger.debug(f"Connection is alive. Source: {message}")
        except asyncio.TimeoutError:
            watchdog_logger.warning(f"{timeout}s timeout elapsed without activity!")
            raise ConnectionError("Server timeout")


async def ping_pong(
    host: str,
    port: int,
    account_hash: str,
    status_updates_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
    timeout: int = 10,
    delay: int = 5,
):
    while True:
        try:
            async with asyncio.timeout(timeout):
                await send_chat_message(
                    host, port, "", account_hash, status_updates_queue
                )
            watchdog_queue.put_nowait("Ping message sent")
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Error when posting a message: {e}")


async def handle_connection(host, port, post_port, account_hash, filepath):

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    while True:
        try:
            auth = await authorization(host, post_port, account_hash)
            if auth:
                event = gui.NicknameReceived(auth.get("nickname"))
                status_updates_queue.put_nowait(event)
                logger.info(
                    f"Authorization has been performed. User {auth.get('nickname')}"
                )

            await load_chat_history(filepath, messages_queue)

            async with anyio.create_task_group() as tg:
                tg.start_soon(
                    gui.draw, messages_queue, sending_queue, status_updates_queue
                )
                tg.start_soon(
                    read_msgs,
                    host,
                    port,
                    messages_queue,
                    history_queue,
                    status_updates_queue,
                    watchdog_queue,
                )
                tg.start_soon(save_messages, filepath, history_queue)
                tg.start_soon(
                    send_msgs,
                    host,
                    post_port,
                    account_hash,
                    sending_queue,
                    status_updates_queue,
                    watchdog_queue,
                )
                tg.start_soon(watch_for_connection, watchdog_queue)
                tg.start_soon(
                    ping_pong,
                    host,
                    post_port,
                    account_hash,
                    status_updates_queue,
                    watchdog_queue,
                )

        except ConnectionError as e:
            logger.warning(f"Connection lost: {e}")
            await anyio.sleep(5)
            continue
        except InvalidToken:
            gui.show_message_box(
                "Invalid token", "Check the token. The server didn't recognize it"
            )
            break


async def main():
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("CHAT_PORT", 5000)
    post_port = env.int("POSTING_PORT", 5050)
    filepath = "minechat.history"
    account_hash = await get_account_hash()

    await handle_connection(host, port, post_port, account_hash, filepath)


if __name__ == "__main__":
    asyncio.run(main())
