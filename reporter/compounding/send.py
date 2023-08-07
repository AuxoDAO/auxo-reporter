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
    ARV,
)
from reporter.models.ERC20 import AUXO_TOKEN_NAMES, ERC20Amount
from reporter.models.Reward import RewardSummary
from reporter.models.SafeTx import (
    ARVIncreaseAmountForManyTx,
    PRVCompoundDepositForSafeTx,
)
from reporter.models.types import EthereumAddress, RewardsByAccount

from reporter.rewards import compute_rewards


def recipients_to_accounts(recipients: RecipientMerkleClaim, token: AUXO_TOKEN_NAMES) -> list[Account]:
    """
    Converts a dictionary of recipients to a list of accounts
    """
    return [
        Account(
            address=address,
            token=WETH(amount=data.rewards),
            rewards=ARV(amount='0') if token == 'ARV' else  PRV(amount="0"),
            state=AccountState.ACTIVE,
        )
        for address, data in recipients.items()
    ]


def compute_pro_rata_auxo(
    recipients: RecipientMerkleClaim,
    total_rewards: BigNumber,
    reward_token: AUXO_TOKEN_NAMES,
):
    """
    Allocates an Auxo derivative token to the recipients based on how much WETH they compounded
    Allocation is computed on a pro-rata basis based on the total amount of WETH compounded
    """
    total_weth = sum(Decimal(recipient.rewards) for recipient in recipients.values())
    accounts = recipients_to_accounts(recipients, reward_token)

    reward = (
        ARV(amount=total_rewards)
        if reward_token == "ARV"
        else PRV(amount=total_rewards)
    )

    return compute_rewards(reward, total_weth or Decimal(0), accounts)


def create_safe_tx(compound_data, reward_token: AUXO_TOKEN_NAMES):
    """
    Switcher to create a PRV staking tx or an ARV staking tx
    """
    return (
        PRVCompoundDepositForSafeTx(compound_data)
        if reward_token == "PRV"
        else ARVIncreaseAmountForManyTx(compound_data)
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

    accounts, summary = compute_pro_rata_auxo(recipients, rewards.amount, token)
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

    compound_data = cast(
        RewardsByAccount,
        [[a.address, a.rewards.amount] for a in accounts],
    )
    safe_tx = create_safe_tx(compound_data, token)
    # safe_tx = create_safe_tx(compound_data, "PRV")
    writer.to_json(safe_tx.dict(), f"safe-tx-{token}")
