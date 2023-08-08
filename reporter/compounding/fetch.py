import json
from reporter.env import ADDRESSES
from reporter.models.SafeTx import MerkeDistributorClaimMultiDelegatedTx
from reporter.models.types import EthereumAddress
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


def get_compound_claims(
    conf: CompoundConf,
    token: AUXO_TOKEN_NAMES,
    multisig: EthereumAddress = ADDRESSES.MULTISIG_OPS,
) -> RecipientMerkleClaim:
    tree = read_tree(conf, token)
    recipients = get_unclaimed_delegated_recipients(tree, conf, token, multisig)
    return recipients


def create_multi_delegated_tx(
    conf: CompoundConf, token: AUXO_TOKEN_NAMES, recipients: RecipientMerkleClaim
):
    """
    Builds a JSON to populate a gnosis safe transaction
    Safe UI has a bug which prevents just passing the tuple array
    If this has problems another alternative is to pass raw calldata
    """

    tuple_only = create_tuple_array(recipients)
    safe_tx = MerkeDistributorClaimMultiDelegatedTx(conf.distributor(token), tuple_only)
    loc = f"{conf.directory}/{conf.date}/compounding/safe-claim-{token}-{conf.compound_epoch}.json"
    with open(loc, "w") as f:
        json.dump(safe_tx.dict(), f, indent=4)


def fetch_and_write_compounders(
    conf: CompoundConf, token: AUXO_TOKEN_NAMES, multisig: EthereumAddress
):

    recipients = get_compound_claims(conf, token)
    recipient_dict = {recipient: data.dict() for recipient, data in recipients.items()}
    writer = RecipientWriter(conf)
    filename = writer.to_json(recipient_dict, f"recipients-{token}")

    create_multi_delegated_tx(conf, token, recipients)
    return filename
