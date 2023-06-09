from reporter.compounding import distribute_compounded_auxo
from reporter.config import load_conf

if __name__ == "__main__":
    epoch = input(" What is the epoch? ")
    conf = load_conf(f"reports/{epoch}")
    amount = input(" Amount of PRV [in Wei] to distribute ")
    compounding_epoch = input(" Which compounding epoch [0, 1, 2...]")
    filename = lambda token: f"recipients-{token}-{compounding_epoch}.json"
    tokens = ["ARV", "PRV"]
    for token in tokens:
        distribute_compounded_auxo(conf, amount, filename(token))
        name = (
            f"./reports/{epoch}/compounding/compound-{token}-{compounding_epoch}.json"
        )
        print(f"💰💰💰 Created a new compounders file at {name} 💰💰💰")
