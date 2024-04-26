import datetime, aiohttp
from loguru import logger
from fake_useragent import UserAgent

from eth_account.messages import encode_defunct

from .account import Account
from .utils import retry
from settings import *


class Linea:
    def __init__(self, acc: Account) -> None:
        self.acc = acc
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> 'Linea':
        self.session = aiohttp.ClientSession(headers={'User-Agent': UserAgent().random})
        return self
    
    async def __aexit__(self, *exc) -> None:
        await self.session.close()

    async def make_request(self, method: str, url: str, **kwargs) -> tuple[int, dict | str] | tuple[None, None]:
        try:
            async with self.session.request(method, url, proxy=self.acc.proxy, **kwargs) as response:
                return response.status, await response.json()
        except aiohttp.ClientConnectorError:
            logger.error(f'{self.acc.info} Не удалось подключиться к прокси: {self.acc.proxy}')
            return None, None
        except aiohttp.ContentTypeError:
            return response.status, await response.text()
    
    async def get_signature_text(self) -> str | None:
        status, data = await self.make_request(
            method='GET',
            url='https://referrals-api.sepolia.linea.build/nonce'
        )
        if status != 200 or len(data) != 17:
            raise Exception(f'{self.acc.info} Не получить nonce | Код: {status} Ответ: {data}')
        return (
            f"referrals.linea.build wants you to sign in with your Ethereum account:\n"
            f"{self.acc.address}\n\n"
            f"Verify wallet ownership for the Linea Surge Referrals\n\n"
            f"URI: https://referrals.linea.build\n"
            f"Version: 1\n"
            f"Chain ID: 59144\n"
            f"Nonce: {data}\n"
            f"Issued At: {datetime.datetime.now().isoformat()[:-3] + 'Z'}"
        )

    async def login(self) -> None:
        text = await self.get_signature_text()
        signed_message = self.acc.account.sign_message(encode_defunct(text=text))
        signature = signed_message.signature.hex()

        status, data = await self.make_request(
            method='POST',
            url='https://referrals-api.sepolia.linea.build/verify',
            json={'message': text, 'signature': signature}
        )
        if status == 200 and data.get('ok') == True:
            return
        raise Exception(f'{self.acc.info} Не удалось пройти верификацию! | Код: {status} Ответ: {data}')

    @retry
    async def register(self) -> None:
        await self.login()
        status, data = await self.make_request(
            method='POST',
            url=f'https://referrals-api.sepolia.linea.build/activate',
            json={'address': self.acc.address, "refCode": REF_CODE},
        )
        if status == 200 and data.get('address') == self.acc.address.lower():
            logger.success(f'{self.acc.info} Успешно зарегистрировался!')
            return
        raise Exception(f'{self.acc.info} Не удалось зарегистрироваться! | Код: {status} Ответ: {data}')
