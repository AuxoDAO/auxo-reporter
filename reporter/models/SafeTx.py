from pathlib import Path
from typing import Any
import json
import time
from pydantic import BaseModel

from reporter.env import ADDRESSES
from reporter.models.types import BigNumber, EthereumAddress


class SafeTxMeta(BaseModel):
    name: str = "Transactions Batch"
    description: str = ""
    txBuilderVersion: str = "1.41.1"
    createdFromSafeAddress: str = ADDRESSES.MULTISIG_OPS
    createdFromOwnerAddress: str = ""
    checksum: str = ""


class TxInput(BaseModel):
    internalType: str
    name: str
    type: str


class SafeContractMethod(BaseModel):
    inputs: list[TxInput]
    name: str
    payable: bool = False


class SafeTxTransaction(BaseModel):
    to: str
    value: str = "0"
    data: str | None = None
    contractMethod: SafeContractMethod
    contractInputsValues: dict[str, Any]


class SafeTx(BaseModel):
    version: str = "1.0"
    chainId: str = "1"
    createdAt: int
    meta: SafeTxMeta
    transactions: list[SafeTxTransaction]


class PRVCompoundDepositForSafeTx(SafeTx):
    def __init__(self, compound_data: list[tuple[EthereumAddress, BigNumber]]):
        meta = SafeTxMeta()
        # created at is the unix timestamp in whole seconds
        created_at = int(time.time())
        transactions = self._create_transactions(compound_data)
        super().__init__(meta=meta, createdAt=created_at, transactions=transactions)


    def _create_transactions(
        self, compound_data: list[tuple[EthereumAddress, BigNumber]]
    ) -> list[SafeTxTransaction]:
        return [
            self._prv_deposit_for(address, amount) for address, amount in compound_data
        ]

    def _prv_deposit_for(self, address: EthereumAddress, amount: BigNumber) -> SafeTxTransaction:
        return SafeTxTransaction(
            to=ADDRESSES.PRV_ROLLSTAKER,
            contractMethod=SafeContractMethod(
                inputs=[
                    TxInput(internalType="address", name="_receiver", type="address"),
                    TxInput(internalType="uint256", name="_amount", type="uint256"),
                ],
                name="depositFor",
            ),
            contractInputsValues={"_amount": amount, "_receiver": address},
        )

    def write(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.json(), f, indent=4)
