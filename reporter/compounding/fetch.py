import json
from reporter.queries import get_unclaimed_delegated_recipients

from reporter.models import (
    Config,
    AUXO_TOKEN_NAMES,
    EthereumAddress,
    RecipientWriter,
    Claim,
    MerkleTree,
    RecipientMerkleClaim,
)


def read_tree(token: AUXO_TOKEN_NAMES, epoch: str, directory="reports") -> MerkleTree:
    with open(f"{directory}/{epoch}/merkle-tree-{token}.json") as f:
        tree = json.load(f)
    return MerkleTree.parse_obj(tree)


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


def get_compound_claims(
    token: AUXO_TOKEN_NAMES,
    distributor: EthereumAddress,
    block: int,
    directory: str,
    epoch: str,
) -> RecipientMerkleClaim:
    tree = read_tree(token, epoch, directory)
    recipients = get_unclaimed_delegated_recipients(tree, distributor, block)
    return recipients


def fetch_and_write_compounders(
    conf: Config,
    token: AUXO_TOKEN_NAMES,
    distributor: EthereumAddress,
    directory="reports",
):
    block = conf.block_snapshot
    recipients = get_compound_claims(token, distributor, block, directory, conf.date)

    recipient_dict = {recipient: data.dict() for recipient, data in recipients.items()}

    writer = RecipientWriter(conf, directory)
    filename = writer.to_json(recipient_dict, f"recipients-{token}")

    tuple_only = create_tuple_array(recipients)
    writer.to_json(tuple_only, f"recipients-tuple-{token}")
    return filename
