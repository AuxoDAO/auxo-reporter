from reporter.compounding import distribute_compounded_auxo
from reporter.models import CompoundConf
from reporter.models.ERC20 import AUXO_TOKEN_NAMES

if __name__ == "__main__":
    path = input(" Path to compound config file (Ensure it has rewards added) ")
    conf = CompoundConf.from_json(path)

    if conf.rewards.amount == 0:
        print(
            "Rewards amount is 0. Please add rewards to the config file and try again."
        )
        exit(1)

    filename = lambda token: f"recipients-{token}-{conf.compound_epoch}.json"
    tokens: list[AUXO_TOKEN_NAMES] = ["ARV", "PRV"]
    for token in tokens:
        rewards = conf.token_rewards(token)
        distribute_compounded_auxo(conf, token, rewards, filename(token))
        name = f"./reports/{conf.compound_epoch}/compounding/compound-{token}-{conf.compound_epoch}.json"
        print(f"💰💰💰 Created a new compounders file at {name} 💰💰💰")
