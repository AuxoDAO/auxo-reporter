from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
from typing import Union
from pydantic import BaseModel
from multicall import Call, Multicall  # type: ignore
from reporter.config import load_conf
from reporter.models import (
    Account,
    AccountState,
    ClaimsRecipient,
    Config,
    AUXO_TOKEN_NAMES,
    WETH,
    ARVRewardSummary,
    PRVRewardSummary,
    BigNumber,
    EthereumAddress,
)
from reporter.models.ERC20 import PRV

from reporter.queries import w3
from reporter.rewards.common import compute_rewards

EPOCH = "2023-6"
ARV_DISTRIBUTOR = "0x727a21924D9267E49D025a48464324edfcD215B5"
PRV_DISTRIBUTOR = "0x06c88C0FD7296717083C0A449C854005218095c5"
MULTISIG_TREASURY = "0x3bCF3Db69897125Aa61496Fc8a8B55A5e3f245d5"

Bytes32 = str


class MerkleRecipient(ClaimsRecipient):
    proof: list[Bytes32]


RecipientMerkleClaim = dict[EthereumAddress, MerkleRecipient]


class MerkleTree(BaseModel):
    windowIndex: int
    chainId: int
    aggregateRewards: Union[ARVRewardSummary, PRVRewardSummary]
    recipients: RecipientMerkleClaim
    root: Bytes32


def read_tree(token: AUXO_TOKEN_NAMES, epoch: str, directory='reports') -> MerkleTree:
    with open(f"{directory}/{epoch}/merkle-tree-{token}.json") as f:
        tree = json.load(f)
    return MerkleTree.parse_obj(tree)


MulticallIsRewardsDelegated = dict[EthereumAddress, bool]
MulticallIsRewardsClaimed = dict[EthereumAddress, bool]


def multicall_is_compounder(
    recipients: RecipientMerkleClaim,
    distributor: EthereumAddress,
    block_number: int,
) -> MulticallIsRewardsDelegated:

    calls = [
        Call(
            # address to call:
            distributor,
            # function isRewardsDelegate(address _user, address _delegate) public view returns (bool)
            ["isRewardsDelegate(address,address)(bool)", address, MULTISIG_TREASURY],
            # return in a format of {[address]: bool}:
            [[address, None]],
        )
        for address in recipients.keys()
    ]

    # Immediately execute the multicall
    return Multicall(calls, _w3=w3, block_id=block_number)()


def multicall_is_claimed(
    recipients: RecipientMerkleClaim,
    distributor: EthereumAddress,
    block_number: int,
) -> MulticallIsRewardsDelegated:

    calls = [
        Call(
            # address to call:
            distributor,
            # function isClaimed(uint256 _windowIndex, uint256 _accountIndex) public view returns (bool) {
            [
                "isClaimed(uint256,uint256)(bool)",
                recipient.windowIndex,
                recipient.accountIndex,
            ],
            # return in a format of {[address]: bool}:
            [[address, None]],
        )
        for address, recipient in recipients.items()
    ]

    # Immediately execute the multicall
    return Multicall(calls, _w3=w3, block_id=block_number)()


def delegated_and_unclaimed(
    delegated: MulticallIsRewardsDelegated, claimed: MulticallIsRewardsClaimed
) -> list[EthereumAddress]:
    return [
        address
        for address, is_delegated in delegated.items()
        if is_delegated and not claimed[address]
    ]


def get_unclaimed_delegated_recipients(
    tree: MerkleTree, distributor: EthereumAddress, block: int
) -> RecipientMerkleClaim:
    delegated = multicall_is_compounder(tree.recipients, distributor, block)
    claimed = multicall_is_claimed(tree.recipients, distributor, block)
    delegated_but_unclaimed = delegated_and_unclaimed(delegated, claimed)
    return {
        recipient: MerkleRecipient.parse_obj(tree.recipients[recipient])
        for recipient in delegated_but_unclaimed
    }


def get_compound_claims(
    token: AUXO_TOKEN_NAMES, distributor: EthereumAddress, block: int, directory: str
) -> RecipientMerkleClaim:
    tree = read_tree(token, EPOCH, directory)
    recipients = get_unclaimed_delegated_recipients(tree, distributor, block)
    return recipients


@dataclass
class RecipientWriter:
    config: Config
    directory: str = "reports"

    @property
    def path(self) -> str:
        return f"{self.directory}/{self.config.date}/compounding"

    def _create_dir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def increment_filename(self, name):
        """
        Check if the filename exists and if so, append a number to it
        """
        self._create_dir()
        i = 0
        while True:
            filename = f"{name}-{i}.json"
            filename_with_path = f"{self.path}/{filename}"

            if Path(filename_with_path).exists():
                i += 1
            else:
                return filename

    # write to a json file
    def to_json(self, data, name: str = "recipients") -> str:
        postfix_filename = self.increment_filename(name)
        with open(f"{self.path}/{postfix_filename}", "w+") as f:
            json.dump(data, f, indent=4)
        return postfix_filename


#    struct Claim {
#        uint256 windowIndex;
#        uint256 accountIndex;
#        uint256 amount;
#        address token;
#        bytes32[] merkleProof;
#        address account;
#    }
Claim = tuple[int, int, BigNumber, EthereumAddress, list[Bytes32], EthereumAddress]


def create_tuple_array(recipients: RecipientMerkleClaim) -> list[Claim]:
    return [
        (
            recipient.windowIndex,
            recipient.accountIndex,
            recipient.rewards,
            recipient.token,
            recipient.proof,
            address,
        )
        for address, recipient in recipients.items()
    ]


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


def fetch_and_write_compounders(
    conf: Config,
    token: AUXO_TOKEN_NAMES,
    distributor: EthereumAddress,
    directory="reports",
):
    block = conf.block_snapshot
    recipients = get_compound_claims(token, distributor, block, directory)

    recipient_dict = {recipient: data.dict() for recipient, data in recipients.items()}

    writer = RecipientWriter(conf, directory)
    filename = writer.to_json(recipient_dict, f"recipients-{token}")

    tuple_only = create_tuple_array(recipients)
    writer.to_json(tuple_only, f"recipients-tuple-{token}")
    return filename


def split_filename(input: str) -> tuple[str, str]:
    """
    Splits a filename in the format `name-TOKEN-NUMBER` and returns (token, number)
    """
    _, token, number = input.split("-")
    return token, number.split(".")[0]  # remove .extension


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

