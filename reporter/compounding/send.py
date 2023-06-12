from decimal import Decimal
import json
from typing import cast
from reporter.models import (
    Account,
    AccountState,
    CompoundConf,
    WETH,
    BigNumber,
    RecipientWriter,
    MerkleRecipient,
    RecipientMerkleClaim,
    PRV,
)
from reporter.models.ERC20 import AUXO_TOKEN_NAMES, ERC20Amount
from reporter.models.SafeTx import PRVCompoundDepositForSafeTx
from reporter.models.types import EthereumAddress

from reporter.rewards import compute_rewards


def recipients_to_accounts(recipients: RecipientMerkleClaim) -> list[Account]:
    return [
        Account(
            address=address,
            token=WETH(amount=data.rewards),
            rewards=PRV(amount="0"),
            state=AccountState.ACTIVE,
        )
        for address, data in recipients.items()
    ]


def compute_pro_rata_auxo(recipients: RecipientMerkleClaim, total_rewards: BigNumber):
    total_weth = sum(Decimal(recipient.rewards) for recipient in recipients.values())
    accounts = recipients_to_accounts(recipients)
    return compute_rewards(
        PRV(amount=total_rewards), total_weth or Decimal(0), accounts
    )


def distribute_compounded_auxo(
    conf: CompoundConf,
    token: AUXO_TOKEN_NAMES,
    rewards: ERC20Amount,
    recipients_filename: str,
    directory="reports",
):

    with open(f"{directory}/{conf.date}/compounding/{recipients_filename}") as f:
        recipients = json.load(f)
        recipients = {
            recipient: MerkleRecipient.parse_obj(data)
            for recipient, data in recipients.items()
        }

    accounts, summary = compute_pro_rata_auxo(recipients, rewards.amount)
    combined = {
        **summary.dict(),
        "recipients": [
            {
                **a.dict(),
                "notes": [
                    f"Compounding {token} Rewards for epoch {conf.date}/{conf.compound_epoch}"
                ],
            }
            for a in accounts
        ],
    }

    writer = RecipientWriter(conf)
    writer.to_json(combined, f"compound-{token}")

    compound_data = [[a.address, a.rewards.amount] for a in accounts]
    safe_tx = PRVCompoundDepositForSafeTx(
        cast(list[tuple[EthereumAddress, BigNumber]], compound_data)
    )
    writer.to_json(safe_tx.dict(), f"safe-tx-{token}")
