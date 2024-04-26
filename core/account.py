from web3 import AsyncWeb3, AsyncHTTPProvider, Account as Web3Account
from web3.middleware import async_geth_poa_middleware

from settings import RPC

Web3Account.enable_unaudited_hdwallet_features()


class Account:
    def __init__(self, index: int, key_mnemonic: str, proxy: str | None) -> None:
        self.index = index
        self.proxy = f'http://{proxy}' if proxy else None
        self.w3 = AsyncWeb3(
            provider=AsyncHTTPProvider(RPC),
            middlewares=[async_geth_poa_middleware],
            request_kwargs={'proxy': self.proxy}
        )
        if len(key_mnemonic) == 66: # private key
            self.account = self.w3.eth.account.from_key(private_key=key_mnemonic)
        elif key_mnemonic.count(' ') == 11: # mnemonic
            self.account = self.w3.eth.account.from_mnemonic(mnemonic=key_mnemonic)
        else:
            raise ValueError(f'№{self.index} Incorrect `key_mnemonic`')
        self.address = self.w3.to_checksum_address(self.account.address)
        self.info = f'[№{self.index} - {self.address[:5]}...{self.address[-5:]}]'
        self.registered: bool | None = None
