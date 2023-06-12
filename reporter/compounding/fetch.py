import json
from reporter.queries import get_unclaimed_delegated_recipients
from reporter.models import (
    AUXO_TOKEN_NAMES,
    RecipientWriter,
    Claim,
    MerkleTree,
    CompoundConf,
    RecipientMerkleClaim,
)


def read_tree(conf: CompoundConf, token: AUXO_TOKEN_NAMES) -> MerkleTree:
    with open(f"{conf.directory}/{conf.date}/merkle-tree-{token}.json") as f:
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


def get_compound_claims(conf: CompoundConf, token: AUXO_TOKEN_NAMES) -> RecipientMerkleClaim:
    tree = read_tree(conf, token)
    recipients = get_unclaimed_delegated_recipients(tree, conf, token)
    return recipients


def fetch_and_write_compounders(
    conf: CompoundConf,
    token: AUXO_TOKEN_NAMES
):

    recipients = get_compound_claims(conf, token)
    recipient_dict = {recipient: data.dict() for recipient, data in recipients.items()}
    writer = RecipientWriter(conf)
    filename = writer.to_json(recipient_dict, f"recipients-{token}")
    tuple_only = create_tuple_array(recipients)
    writer.to_json(tuple_only, f"recipients-tuple-{token}")
    return filename
