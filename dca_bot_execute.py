import os
import uvloop
import asyncio
from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv
from paloma_sdk.client.lcd import AsyncLCDClient
from paloma_sdk.key.mnemonic import MnemonicKey
from paloma_sdk.client.lcd.api.tx import CreateTxOptions
from paloma_sdk.core.wasm import MsgExecuteContract
from paloma_sdk.core.coins import Coins


async def pancakeswap_bot():
    node: str = os.environ['BNB_NODE']
    w3: Web3 = Web3(Web3.HTTPProvider(node))
    dca_bot_address: str = os.environ['PANCAKESWAP_DCA_BOT']
    dca_bot_abi: str = os.environ['DCA_BOT_ABI']
    dca_sc: Contract = w3.eth.contract(
        address=dca_bot_address, abi=dca_bot_abi)
    swap_id, amount_out_min, number_trades = dca_sc.functions.triggerable_deposit().call()
    if int(number_trades) > 0 or int(swap_id) > 0 or int(amount_out_min) > 0:
        paloma_lcd = os.environ['PALOMA_LCD']
        paloma_chain_id = os.environ['PALOMA_CHAIN_ID']
        paloma: AsyncLCDClient = AsyncLCDClient(
            url=paloma_lcd, chain_id=paloma_chain_id)
        paloma.gas_prices = "0.01ugrain"
        mnemonic: str = os.environ['PALOMA_KEY']
        acct: MnemonicKey = MnemonicKey(mnemonic=mnemonic)
        wallet = paloma.wallet(acct)
        dca_cw = os.environ['PANCAKESWAP_DCA_BOT_CW']
        tx = await wallet.create_and_sign_tx(
            CreateTxOptions(
                msgs=[
                    MsgExecuteContract(wallet.key.acc_address, dca_cw, {
                        "swap": {"swap_id": swap_id, "amount_out_min": amount_out_min, "number_trades": number_trades}
                    }, Coins())
                ]
            )
        )

        result = await paloma.tx.broadcast(tx)
        print(result)


async def main():
    load_dotenv()
    await pancakeswap_bot()


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
