from reporter.compounding import fetch_and_write_compounders
from reporter.env import ADDRESSES
from reporter.models.Config import CompoundConf

if __name__ == "__main__":
    """
    Parses a config file then writes both ARV and PRV compounders.

    We contain everything to a given epoch. A future improvement would be
    to iterate over all epochs or even make a stateful reporter that fetches all historic
    compounding activity.
    """
    PRV_COMPOUNDING_MULTISIG = ADDRESSES.MULTISIG_OPS
    ARV_COMPOUNDING_MULTISIG = ADDRESSES.MULTISIG_OPS
    

    path = input(" Path to compound config file: ")
    conf = CompoundConf.from_json(path)
    filename = fetch_and_write_compounders(conf, "ARV", ARV_COMPOUNDING_MULTISIG)
    print(
        f"💰💰💰 Created a new compounders file at ./reports/{conf.compound_epoch}/compounding/{filename} 💰💰💰"
    )

    filename = fetch_and_write_compounders(conf, "PRV", PRV_COMPOUNDING_MULTISIG)
    print(
        f"💰💰💰 Created a new compounders file at ./reports/{conf.compound_epoch}/compounding/{filename} 💰💰💰"
    )
