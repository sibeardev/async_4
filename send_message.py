import argparse
import asyncio
import json
import logging
import re

import aiofiles
from environs import Env

from exceptions import InvalidToken

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
            await authorise(reader, writer, account_hash)

            logger.debug(await reader.readline())
            await submit_message(reader, writer, message)

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")
        except InvalidToken as e:
            logger.error(f"Authorization error: {e}")

    except asyncio.CancelledError:
        logger.debug("Chat stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


async def authorise(reader, writer, account_hash):

    try:
        if account_hash is None:
            raise InvalidToken("Empty token")

        clean_hash = sanitize_input(account_hash)
        if not clean_hash:
            raise InvalidToken("Invalid token format")

        writer.write(f"{clean_hash}\n".encode())
        await writer.drain()
        raw_response = await reader.readline()
        response_text = raw_response.decode().strip()
        auth = json.loads(response_text)

        if auth is None:
            raise InvalidToken("Unknown token")

    except ConnectionError as e:
        logger.error(f"Connection error during auth: {e}")
        raise

    return auth


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
    return re.sub(r"[\r\n]+", " ", text).strip()


def parse_args(host, port):
    parser = argparse.ArgumentParser(
        description="Client for connecting to the chat room",
    )
    parser.add_argument(
        "--host",
        default=host,
        help="Chat Server Host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=port,
        help="Chat Server Port",
    )
    parser.add_argument(
        "--message",
        required=True,
        type=str,
        help="Message Text",
    )
    return parser.parse_args()


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
    args = parse_args(host, port)
    await send_chat_message(args.host, args.port, args.message, account_hash)


if __name__ == "__main__":
    asyncio.run(main())
