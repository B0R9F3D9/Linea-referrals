import asyncio, aiohttp
from tabulate import tabulate

from .account import Account
from .linea import Linea
from .utils import retry


class Checker:
    def __init__(self, accs: list[Account]) -> None:
        self.accs = accs

    async def check_proxy(self, acc: Account) -> str | None:
        if acc.proxy:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org', proxy=acc.proxy) as resp:
                    if resp.status == 200:
                        if await resp.text() == acc.proxy.split('@')[1].split(':')[0]:
                            return '-✅'
                        return '-❗️'
                    return '-❌'

    @retry
    async def check(self, acc: Account) -> dict:
        async with Linea(acc) as linea:
            status, data = await linea.make_request(
                method='GET',
                url=f'https://referrals-api.sepolia.linea.build/query/{acc.address}',
            )
        if data == None:
            raise Exception(f'{acc.info} Не удалось проверить аккаунт | Код: {status} Ответ: {data}')
        acc.registered = True if data.get('address') == acc.address.lower() else False
        proxy_status = await self.check_proxy(acc)
        return {
            '№': acc.index,
            'Адрес': f'{acc.address[:5]}...{acc.address[-5:]}',
            'Прокси-статус': acc.proxy.split('@')[1]+proxy_status if acc.proxy else 'Не указан',
            'Зареган': data['timestamp'].split('T')[0] if acc.registered else '❌',
            'По чьей рефке': f'{data["referrer"][:5]}...{data["referrer"][-5:]}' if acc.registered else '❌',
            'Рефка': data['code'] if acc.registered else '❌',
            'Рефов': len(data['referrals']) if acc.registered else '❌',
        }

    async def run(self) -> None:
        tasks = [asyncio.create_task(self.check(acc)) for acc in self.accs]
        results = await asyncio.gather(*tasks)
        print(tabulate(results, headers='keys', tablefmt='rounded_outline'))
    