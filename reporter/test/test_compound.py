import json
from reporter.compounding.compound import (
    fetch_and_write_arv_compounders,
    distribute_compounded_auxo,
)
from reporter.config import create_conf
from reporter.test.conftest import TEST_REPORTS_DIR
from reporter.test.stubs.compound.create_compound_stubs import (
    CLAIMOOORS,
    COMPOUNDERS,
    NON_COMPOUNDOORS,
    create_mock_tree,
    create_is_claimed_response,
    create_is_compounder_response,
)


def test_create_mock_tree():
    create_mock_tree()


def test_main(monkeypatch):
    monkeypatch.setattr(
        "reporter.compounding.compound.multicall_is_claimed",
        lambda *_: create_is_claimed_response(),
    )

    monkeypatch.setattr(
        "reporter.compounding.compound.multicall_is_compounder",
        lambda *_: create_is_compounder_response(),
    )

    conf = create_conf("config/6-23.json")
    fetch_and_write_arv_compounders(conf, TEST_REPORTS_DIR)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-0.json") as f:
        recipients = json.load(f)
    assert recipients
    assert len(recipients) == len(COMPOUNDERS)

    assert not any(address in recipients for address in NON_COMPOUNDOORS)
    assert not any(address in recipients for address in CLAIMOOORS)

    assert all(address in recipients for address, _ in COMPOUNDERS)

    # check file is incremented if run again
    fetch_and_write_arv_compounders(conf, TEST_REPORTS_DIR)

    with open(f"{TEST_REPORTS_DIR}/{conf.date}/compounding/recipients-1.json") as f:
        assert recipients == json.load(f)
    

    # now assume we distribute
    distribute_compounded_auxo(conf, "333888084700000000000", "recipients-0.json", TEST_REPORTS_DIR)
