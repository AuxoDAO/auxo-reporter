from decimal import Decimal
import pytest
import json
from reporter.compounding import (
    fetch_and_write_compounders,
    distribute_compounded_auxo,
)
from reporter.env import ADDRESSES
from reporter.models import CompoundConf
from reporter.models.Config import CompoundConf
from reporter.models.ERC20 import ARV, AUXO_TOKEN_NAMES, PRV
from reporter.test.conftest import TEST_REPORTS_DIR
from reporter.test.stubs.compound.compounders import TestDataARV, TestDataPRV
from reporter.test.stubs.compound.create_compound_stubs import (
    create_mock_tree,
    create_is_claimed_response,
    create_is_compounder_response,
    get_compounder_by_address,
)

ARV_DISTRIBUTOR = ADDRESSES.ARV_DISTRIBUTOR
PRV_DISTRIBUTOR = ADDRESSES.PRV_DISTRIBUTOR

# --------- FIXTURES ---------


@pytest.fixture(scope="module")
def conf() -> CompoundConf:
    return CompoundConf(
        block_snapshot=12345678,
        year=2023,
        month=6,
        directory=TEST_REPORTS_DIR,
        compound_epoch=0,
        rewards=PRV(amount=0),
        arv_percentage=50
    )


# creates a merkle tree using sample data
@pytest.fixture(autouse=True, scope="module")
def setup(conf: CompoundConf):
    create_mock_tree(TestDataARV, "ARV", f"{TEST_REPORTS_DIR}/{conf.date}")
    create_mock_tree(TestDataPRV, "PRV", f"{TEST_REPORTS_DIR}/{conf.date}")


@pytest.fixture(scope="function")
def recipients_arv(monkeypatch, conf: CompoundConf):

    monkeypatch.setattr(
        "reporter.queries.compound.multicall_is_claimed",
        lambda *_: create_is_claimed_response(TestDataARV),
    )

    monkeypatch.setattr(
        "reporter.queries.compound.multicall_is_compounder",
        lambda *_: create_is_compounder_response(TestDataARV),
    )

    fetch_and_write_compounders(conf, "ARV", ADDRESSES.MULTISIG_OPS)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-ARV-0.json") as f:
        recipients = json.load(f)
    return recipients


@pytest.fixture(scope="function")
def recipients_prv(monkeypatch, conf: CompoundConf):
    monkeypatch.setattr(
        "reporter.queries.compound.multicall_is_claimed",
        lambda *_: create_is_claimed_response(TestDataPRV),
    )

    monkeypatch.setattr(
        "reporter.queries.compound.multicall_is_compounder",
        lambda *_: create_is_compounder_response(TestDataPRV),
    )

    fetch_and_write_compounders(conf, "PRV", ADDRESSES.MULTISIG_OPS)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-PRV-0.json") as f:
        recipients = json.load(f)
    return recipients


# --------- TESTS ---------


def test_get_compounding_recipients(recipients_arv: dict, recipients_prv: dict):
    assert recipients_arv
    assert len(recipients_arv) == len(TestDataARV.COMPOUNDERS)

    assert not any(address in recipients_arv for address in TestDataARV.NON_COMPOUNDERS)
    assert not any(address in recipients_arv for address in TestDataARV.CLAIMOORS)

    assert all(c.address in recipients_arv for c in TestDataARV.COMPOUNDERS)

    assert recipients_prv
    assert len(recipients_prv) == len(TestDataPRV.COMPOUNDERS)

    assert not any(address in recipients_prv for address in TestDataPRV.NON_COMPOUNDERS)
    assert not any(address in recipients_prv for address in TestDataPRV.CLAIMOORS)

    assert all(c.address in recipients_prv for c in TestDataPRV.COMPOUNDERS)


def safe_tx_reward_prv(address: str, safe_tx: dict) -> str:
    """
    Returns the amount of PRV that was sent to `address` in the safe tx
    You can check this matches the original value in the compounders file
    """
    for transaction in safe_tx["transactions"]:
        if transaction["contractInputsValues"]["_receiver"] == address:
            return transaction["contractInputsValues"]["_amount"]
    raise Exception(f"Could not find {address} in safe tx")


def safe_tx_reward_arv(address: str, safe_tx: dict) -> str:
    """
    Returns the amount of ARV that was sent to `address` in the safe tx
    You can check this matches the original value in the compounders file
    """

    assert (
        len(safe_tx["transactions"]) == 1
    ), "Should only be one transaction in safe tx"
    transaction = safe_tx["transactions"][0]
    receivers = json.loads(transaction["contractInputsValues"]["_receivers"])

    for idx, r in enumerate(receivers):
        if r == address:
            return json.loads(transaction["contractInputsValues"]["_amountNewTokens"])[
                idx
            ]

    raise Exception(f"Could not find {address} in safe tx")


def safe_tx_reward(address: str, safe_tx: dict, token: AUXO_TOKEN_NAMES) -> str:
    if token == "PRV":
        return safe_tx_reward_prv(address, safe_tx)
    elif token == "ARV":
        return safe_tx_reward_arv(address, safe_tx)
    else:
        raise Exception(f"Invalid token {token}")


def test_compound_distribution(conf: CompoundConf):
    params = [
        ["333888084700000000000", "ARV", TestDataARV, True],
        ["100000000000000000000", "PRV", TestDataPRV, False],
    ]

    for total, token, testData, run_loop in params:
        distribute_compounded_auxo(
            conf,
            token,
            PRV(amount=total) if token == "PRV" else ARV(amount=total),
            f"recipients-{token}-0.json",
            TEST_REPORTS_DIR,
        )

        with open(
            f"{TEST_REPORTS_DIR}/{conf.date}/compounding/compound-{token}-0.json"
        ) as f:
            compounded = json.load(f)

        with open(
            f"{TEST_REPORTS_DIR}/{conf.date}/compounding/safe-tx-{token}-0.json"
        ) as o:
            safe_tx = json.load(o)

        # check some basics
        assert compounded
        assert len(compounded["recipients"]) == len(testData.COMPOUNDERS)
        assert compounded["amount"] == total

        # totalling rewards should equal the passed total
        total_rewards_aggregated = sum(
            Decimal(recipient["rewards"]["amount"])
            for recipient in compounded["recipients"]
        )
        assert abs(total_rewards_aggregated - Decimal(compounded["amount"])) < Decimal(
            100
        )

        # check the correct reward token
        assert all(
            recipient["rewards"]["symbol"] == token
            for recipient in compounded["recipients"]
        )

        # check that we can find in the safe tx
        for recipient in compounded["recipients"]:
            assert safe_tx_reward(recipient["address"], safe_tx, token) == str(
                recipient["rewards"]["amount"]
            )

        if not run_loop:
            continue

        for recipient in compounded["recipients"]:
            reward_amount = Decimal(recipient["rewards"]["amount"])
            compounder = get_compounder_by_address(
                recipient["address"], TestDataARV.COMPOUNDERS
            )
            expected_reward = Decimal(compounder.auxo_compound)
            diff = abs(reward_amount - expected_reward)
            # TODO understand why the rounding is 5 gwei
            assert diff <= Decimal(5000000000)  # 5 GWEI
