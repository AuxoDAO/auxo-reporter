from reporter.compounding import fetch_and_write_compounders
from reporter.env import ADDRESSES
from reporter.config import load_conf 

if __name__ == "__main__":
    """
    Should we be doing by epoch?
    Could we instead just get ALL delegates
    Then we go over all epochs
    - Each time the reporter exhausts all epochs, so in theory we can just run
      under the assumption that all previous epochs are fully accounted for

    2 modes: USE DB (Happy Path) vs. SCAN everything (SLOW)
    """
    epoch = input(" What is the epoch? ")
    conf = load_conf(f"reports/{epoch}")

    filename = fetch_and_write_compounders(conf, 'ARV', ADDRESSES.ARV_DISTRIBUTOR)
    print(
        f"💰💰💰 Created a new compounders file at ./reports/{epoch}/compounding/{filename} 💰💰💰"
    )

    filename = fetch_and_write_compounders(conf, 'PRV', ADDRESSES.PRV_DISTRIBUTOR)
    print(
        f"💰💰💰 Created a new compounders file at ./reports/{epoch}/compounding/{filename} 💰💰💰"
    )
