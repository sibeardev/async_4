import asyncio
import json
import logging
import os

import aiofiles
from environs import Env

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def write_to_chat(host, port, message, account_hash):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        logger.debug(await reader.readline())

        try:
            if account_hash:
                writer.write(f"{account_hash}\n".encode())
                await writer.drain()

                raw_response = await reader.readline()
                response_text = raw_response.decode().strip()
                auth_result = json.loads(response_text)
                if auth_result is None:
                    logger.warning(
                        "Неизвестный токен. Проверьте его или зарегистрируйте заново."
                    )
                    return
                logger.debug(response_text)

            logger.debug(await reader.readline())

            writer.write(f"{message}\n\n".encode())
            await writer.drain()
            logger.debug(await reader.readline())

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")

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
    port = env.int("POSTING_PORT", 5050)

    try:
        async with aiofiles.open("token.json", "r") as file:
            user_token = json.loads(await file.read())
    except FileNotFoundError:
        logger.info("Authorization file not found! run `python3 register.py`")
        return

    message = "HELLO WORLD!"
    await write_to_chat(host, port, message, user_token["account_hash"])


if __name__ == "__main__":
    asyncio.run(main())
