import asyncio, random
from loguru import logger

from settings import RETRY_COUNT


async def sleep(sleep_from: int, sleep_to: int):
    delay = random.randint(sleep_from, sleep_to)
    logger.info(f'Спим {delay} секунд...')
    for _ in range(delay):
        await asyncio.sleep(1)

def retry(func):
    async def wrapper(*args, **kwargs):
        for i in range(1, RETRY_COUNT+1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if args and hasattr(args[0], '__class__'): 
                    logger.error(f'({args[0].__class__.__name__ }.{func.__name__} {i}/{RETRY_COUNT}): {e}')
                else:
                    logger.error(f'({func.__name__} {i}/{RETRY_COUNT}): {e}')
                if i != RETRY_COUNT: await sleep(20, 30)
    return wrapper
