from decimal import Decimal
import pytest
import json
from reporter.compounding import (
    fetch_and_write_arv_compounders,
    distribute_compounded_auxo,
)
from reporter.config import create_conf
from reporter.models.Config import Config
from reporter.test.conftest import TEST_REPORTS_DIR
from reporter.test.stubs.compound.create_compound_stubs import (
    CLAIMOOORS,
    COMPOUNDERS,
    NON_COMPOUNDOORS,
    create_mock_tree,
    create_is_claimed_response,
    create_is_compounder_response,
    get_compounder_by_address,
)

# --------- FIXTURES ---------

# creates a merkle tree using sample data
@pytest.fixture(autouse=True, scope="module")
def setup():
    create_mock_tree()


@pytest.fixture(scope="module")
def conf() -> Config:
    return create_conf("config/6-23.json")


@pytest.fixture(scope="function")
def recipients(monkeypatch, conf: Config):

    monkeypatch.setattr(
        "reporter.compounding.multicall_is_claimed",
        lambda *_: create_is_claimed_response(),
    )

    monkeypatch.setattr(
        "reporter.compounding.multicall_is_compounder",
        lambda *_: create_is_compounder_response(),
    )

    fetch_and_write_arv_compounders(conf, TEST_REPORTS_DIR)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-0.json") as f:
        recipients = json.load(f)
    return recipients


# --------- TESTS ---------


def test_get_compounding_recipients(recipients: dict):
    assert recipients
    assert len(recipients) == len(COMPOUNDERS)

    assert not any(address in recipients for address in NON_COMPOUNDOORS)
    assert not any(address in recipients for address in CLAIMOOORS)

    assert all(c.address in recipients for c in COMPOUNDERS)


def test_multiple_compounding_increments_filename(conf: Config, recipients: dict):
    fetch_and_write_arv_compounders(conf, TEST_REPORTS_DIR)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-1.json") as f:
        assert recipients == json.load(f)


def test_compound_distribution(conf: Config):
    distribute_compounded_auxo(
        conf, "333888084700000000000", "recipients-0.json", TEST_REPORTS_DIR
    )

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/compound-0.json") as f:
        compounded = json.load(f)

    # check some basics
    assert compounded
    assert len(compounded["recipients"]) == len(COMPOUNDERS)
    assert compounded["amount"] == "333888084700000000000"

    # totalling rewards should equal the passed total
    total_rewards_aggregated = sum(
        Decimal(recipient["rewards"]["amount"])
        for recipient in compounded["recipients"]
    )
    assert abs(total_rewards_aggregated - Decimal(compounded["amount"])) < Decimal(100)

    for recipient in compounded["recipients"]:
        reward_amount = Decimal(recipient["rewards"]["amount"])
        compounder = get_compounder_by_address(recipient["address"])
        expected_reward = Decimal(compounder.auxo_compound)
        diff = abs(reward_amount - expected_reward)
        print(f"reward {reward_amount} expected {expected_reward} diff {diff}")
        # TODO this looks bad, so need to check
        assert diff <= Decimal(5000000000)  # 5 GWEI
