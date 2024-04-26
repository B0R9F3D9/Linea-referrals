import datetime, sys, random, asyncio
from loguru import logger
from questionary import Choice, select

from core.account import Account
from core.linea import Linea
from core.checker import Checker
from core.utils import sleep
from settings import *


async def run() -> None:
    if SHUFFLE_ACCS:
        random.shuffle(accs)
    for acc in accs:
        if acc.registered:
            logger.info(f'{acc.info} Уже зарегистрирован ранее! Пропускаем...')
            continue
        async with Linea(acc) as linea:
            await linea.register()
        if acc != accs[-1]:
            await sleep(*SLEEP_BETWEEN_ACCS)

async def main() -> None:
    module = await select(
        message='Выберите модуль: ',
        instruction='(используйте стрелочки для навигации)',
        choices=[
            Choice('🚀 Запуск', run),
            Choice('📊 Чекер', 'checker'),
            Choice('❌ Выход', 'exit')
        ],
        qmark="\n❓ ",
        pointer="👉 "
    ).ask_async()
    if module == 'checker':
        return
    if module in [None, 'exit']:
        exit()
    await run()


if __name__ == "__main__":
    logger.remove()
    format='<white>{time:HH:mm:ss}</white> | <bold><level>{level: <7}</level></bold> | <level>{message}</level>'
    logger.add(sink=sys.stdout, format=format)
    logger.add(sink=f'logs/{datetime.datetime.today().strftime("%Y-%m-%d")}.log', format=format)

    with open("data/wallets.txt", "r") as file:
        WALLETS = [x.strip() for x in file.readlines()]

    with open('data/proxies.txt', 'r') as file:
        PROXIES = {i: x.strip() for i, x in enumerate(file.readlines(), 1)}

    loop = asyncio.get_event_loop()
    while True:
        try:
            accs = [Account(i, wallet, PROXIES.get(i)) for i, wallet in enumerate(WALLETS, 1)]
            loop.run_until_complete(Checker(accs).run())
            loop.run_until_complete(main())
        except Exception as e:
            logger.critical(e)
        except (KeyboardInterrupt, SystemExit):
            print('\n👋👋👋')
            exit()
