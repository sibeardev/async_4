import asyncio
import logging

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


if __name__ == "__main__":
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("POSTING_PORT", 5050)
    account_hash = env.str("ACCOUNT_HASH")
    message = "HELLO WORLD!"
    asyncio.run(write_to_chat(host, port, message, account_hash))
