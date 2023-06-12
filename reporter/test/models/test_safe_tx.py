import json
from typing import cast

from reporter.models import PRVCompoundDepositForSafeTx
from reporter.models.types import BigNumber, EthereumAddress


def test_safe_tx():
    with open("reporter/test/stubs/compound/multisend/test.json") as j:
        data = json.load(j)

    tx_data = [
        ["0x5f4C208C65Dc8C73F49a3600905dA58680Db4626", "45949549549"],
        ["0xB86D1d1e7b63D602c6e720448cCaA64ca4653c2a", "1"],
    ]

    tx = PRVCompoundDepositForSafeTx(
        cast(list[tuple[EthereumAddress, BigNumber]], tx_data)
    )

    for t in tx.transactions:

        if t.contractInputsValues["_receiver"] == tx_data[0][0]:
            assert t.contractInputsValues["_amount"] == tx_data[0][1]

        if t.contractInputsValues["_receiver"] == tx_data[1][0]:
            assert t.contractInputsValues["_amount"] == tx_data[1][1]
