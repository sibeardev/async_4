import argparse
import asyncio
import json
import logging

import aiofiles
from environs import Env

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def register(host, port, nickname):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        try:
            logger.debug(await reader.readline())
            writer.write("\n".encode())
            await writer.drain()

            logger.debug(await reader.readline())
            writer.write(f"{nickname}\n".encode())
            await writer.drain()

            raw_response = await reader.readline()
            response_text = raw_response.decode().strip()
            auth_result = json.loads(response_text)
            async with aiofiles.open("token.json", mode="w") as token_file:
                await token_file.write(json.dumps(auth_result, indent=2))
            logger.debug(raw_response)

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")

    except asyncio.CancelledError:
        logger.debug("Chat stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")


def parse_args(host, port):
    parser = argparse.ArgumentParser(
        description="Client for chat registration",
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
        "--nickname",
        type=str,
        help="User Name",
    )
    return parser.parse_args()


if __name__ == "__main__":
    env = Env()
    env.read_env()
    host = env.str("HOST")
    port = env.int("POSTING_PORT", 5050)
    args = parse_args(host, port)
    nickname = args.nickname if args.nickname else "anonymous"
    account_hash = asyncio.run(register(args.host, args.port, nickname))
