import asyncio
import json
import logging
import re

import aiofiles
from environs import Env

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def send_chat_message(host, port, message, account_hash):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        try:
            logger.debug(await reader.readline())
            if await authorise(reader, writer, account_hash) is None:
                logger.error("Unknown token. Check it or register it again.")
                return

            logger.debug(await reader.readline())
            await submit_message(reader, writer, message)

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")

    except asyncio.CancelledError:
        logger.debug("Chat stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


async def authorise(reader, writer, account_hash):
    clean_hash = sanitize_input(account_hash)
    if not clean_hash:
        logger.error("Invalid token format")
        return

    try:
        writer.write(f"{account_hash}\n".encode())
        await writer.drain()

        raw_response = await reader.readline()
        response_text = raw_response.decode().strip()

    except ConnectionError as e:
        logger.error(f"Connection error during auth: {e}")
        raise

    return json.loads(response_text)


async def submit_message(reader, writer, message):
    clean_message = sanitize_input(message)
    if not clean_message:
        logger.error("Message cannot be empty")
        return
    try:
        writer.write(f"{clean_message}\n\n".encode())
        await writer.drain()
        logger.debug(await reader.readline())
    except ConnectionError as e:
        logger.error(f"Connection error during auth: {e}")
        raise


def sanitize_input(text):
    if text is None:
        return
    return re.sub(r"[\r\n]+", " ", text).strip()


async def main():
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("POSTING_PORT", 5050)

    try:
        async with aiofiles.open("token.json", "r") as file:
            user_token = json.loads(await file.read())
    except FileNotFoundError:
        logger.info("Authorization file not found! run `python3 register.py`")
        return
    account_hash = user_token.get("account_hash", None)
    message = "HELLO"
    await send_chat_message(host, port, message, account_hash)


if __name__ == "__main__":
    asyncio.run(main())
