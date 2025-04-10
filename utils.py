import asyncio
import json
import logging

import aiofiles

logger = logging.getLogger(__name__)


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
