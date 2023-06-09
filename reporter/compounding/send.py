from decimal import Decimal
import json
from typing import cast
from reporter.models import (
    Account,
    AccountState,
    Config,
    WETH,
    BigNumber,
    RecipientWriter,
    MerkleRecipient,
    RecipientMerkleClaim,
    PRV,
)
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


def split_filename(input: str) -> tuple[str, str]:
    """
    Splits a filename in the format `name-TOKEN-NUMBER` and returns (token, number)
    """
    _, token, number = input.split("-")
    return token, number.split(".")[0]  # remove .extension


def create_erc20_transfer_transaction():
    """
    Take the recipients object and construct a bulk ERC20 transfer transaction in JSON
    """


# TODO compounding config
def distribute_compounded_auxo(
    conf: Config, amount: str, recipients_filename: str, directory="reports"
):

    with open(f"{directory}/{conf.date}/compounding/{recipients_filename}") as f:
        recipients = json.load(f)
        recipients = {
            recipient: MerkleRecipient.parse_obj(data)
            for recipient, data in recipients.items()
        }

    accounts, summary = compute_pro_rata_auxo(recipients, amount)
    token, number = split_filename(recipients_filename)
    combined = {
        **summary.dict(),
        "recipients": [
            {
                **a.dict(),
                "notes": [
                    f"Compounding {token} Rewards for epoch {conf.date}/{number}"
                ],
            }
            for a in accounts
        ],
    }

    writer = RecipientWriter(conf, directory)
    writer.to_json(combined, f"compound-{token}")

    compound_data = [[a.address, a.rewards.amount] for a in accounts]
    safe_tx = PRVCompoundDepositForSafeTx(
        cast(list[tuple[EthereumAddress, BigNumber]], compound_data)
    )
    writer.to_json(safe_tx.dict(), f"safe-tx-{token}")
