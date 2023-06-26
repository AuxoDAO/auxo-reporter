from pathlib import Path
from typing import Any
import json
import time
from pydantic import BaseModel

from reporter.env import ADDRESSES
from reporter.models.Claim import Claim
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


class TxComponent(TxInput):
    components: list[TxInput]


class SafeContractMethod(BaseModel):
    inputs: list[TxInput | TxComponent]
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

    def write(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.json(), f, indent=4)


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

    def _prv_deposit_for(
        self, address: EthereumAddress, amount: BigNumber
    ) -> SafeTxTransaction:
        return SafeTxTransaction(
            to=ADDRESSES.PRV_ROLLSTAKER,
            # order is important here - values and type declarations must match
            contractMethod=SafeContractMethod(
                inputs=[
                    TxInput(internalType="uint256", name="_amount", type="uint256"),
                    TxInput(internalType="address", name="_receiver", type="address"),
                ],
                name="depositFor",
            ),
            contractInputsValues={"_amount": amount, "_receiver": address},
        )


class MerkeDistributorClaimMultiDelegatedTx(SafeTx):

    def __init__(self, distributor: EthereumAddress, claims: list[Claim]):
        meta = SafeTxMeta()
        # created at is the unix timestamp in whole seconds
        created_at = int(time.time())
        transactions = self._create_transactions(claims, distributor)
        super().__init__(meta=meta, createdAt=created_at, transactions=transactions)

    def _create_transactions(self, claims: list[Claim], distributor: EthereumAddress) -> list[SafeTxTransaction]:
        return [
            SafeTxTransaction(
                to=distributor,
                contractInputsValues={"_claims": json.dumps(claims)},
                contractMethod=SafeContractMethod(
                    inputs=[
                        TxComponent(
                            internalType="struct IMerkleDistributor.Claim[]",
                            name="_claims",
                            type="tuple[]",
                            components=[
                                TxInput(
                                    internalType="uint256",
                                    name="windowIndex",
                                    type="uint256",
                                ),
                                TxInput(
                                    internalType="uint256",
                                    name="accountIndex",
                                    type="uint256",
                                ),
                                TxInput(
                                    internalType="uint256",
                                    name="amount",
                                    type="uint256",
                                ),
                                TxInput(
                                    internalType="address",
                                    name="token",
                                    type="address",
                                ),
                                TxInput(
                                    internalType="bytes32[]",
                                    name="merkleProof",
                                    type="bytes32[]",
                                ),
                                TxInput(
                                    internalType="address",
                                    name="account",
                                    type="address",
                                ),
                            ],
                        )
                    ],
                    name="claimMultiDelegated",
                ),
            )
        ]
