import json
from pathlib import Path
from reporter.models.ERC20 import AUXO_TOKEN_NAMES
from reporter.models.types import EthereumAddress
from reporter.test.stubs.compound.compounders import Compounder
from reporter.test.stubs.compound.compounders import TestData

TREE_PATH = "reporter/test/stubs/compound"


def get_compounder_by_address(
    address: EthereumAddress, compounders: list[Compounder]
) -> Compounder:
    for c in compounders:
        if c.address == address:
            return c

    raise Exception(f"Compounder with address {address} not found")


def create_is_claimed_response(data: TestData) -> dict[EthereumAddress, bool]:
    res = {}

    for c in data.COMPOUNDERS:
        res[c.address] = False

    for address in data.NON_COMPOUNDERS:
        res[address] = False

    for address in data.CLAIMOORS:
        res[address] = True

    return res


def create_is_compounder_response(data: TestData) -> dict[EthereumAddress, bool]:
    res = {}

    for c in data.COMPOUNDERS:
        res[c.address] = True

    for address in data.CLAIMOORS:
        res[address] = True

    for address in data.NON_COMPOUNDERS:
        res[address] = False

    return res


def create_mock_tree(data: TestData, token: AUXO_TOKEN_NAMES, destination: str):
    # read the source merkle tree
    with open(f"{TREE_PATH}/original/merkle-tree-base.json") as f:
        tree = json.load(f)

    # save recipients and clear out - we will be replacing them
    recipient_data = list(tree["recipients"].values())
    tree["recipients"] = {}

    # replace the first len(COMPOUNDERS) recipients with the COMPOUNDERS addresses and rewards
    for i, c in enumerate(data.COMPOUNDERS):
        tree["recipients"][c.address] = recipient_data[i]
        tree["recipients"][c.address]["rewards"] = c.weth_rewards

    # replace the next len(data.NON_COMPOUNDERS) recipients with the data.NON_COMPOUNDERS addresses
    for i, address in enumerate(data.NON_COMPOUNDERS):
        tree["recipients"][address] = recipient_data[i + len(data.COMPOUNDERS)]

    # replace the next len(data.CLAIMOORS) recipients with the data.CLAIMOORS addresses
    for i, address in enumerate(data.CLAIMOORS):
        tree["recipients"][address] = recipient_data[
            i + len(data.COMPOUNDERS) + len(data.NON_COMPOUNDERS)
        ]

    assert len(tree["recipients"]) == len(data.COMPOUNDERS) + len(
        data.NON_COMPOUNDERS
    ) + len(data.CLAIMOORS)

    # save our new tree
    Path(destination).mkdir(parents=True, exist_ok=True)
    with open(f"{destination}/merkle-tree-{token}.json", "w") as f:
        json.dump(tree, f, indent=2)
