import asyncio
import json
import logging
import re

import aiofiles

import gui
from exceptions import InvalidToken

logger = logging.getLogger(__name__)


async def send_chat_message(host, port, message, account_hash, status_updates_queue):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    try:
        reader, writer = await asyncio.open_connection(host, port)
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
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
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)


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

            return auth_result["account_hash"]

        except (ConnectionError, asyncio.IncompleteReadError) as e:
            logger.error(f"Connection error: {e}")

    except asyncio.CancelledError:
        logger.debug("Chat stopped")

    finally:
        writer.close()
        await writer.wait_closed()
        logger.debug("Connection closed")
