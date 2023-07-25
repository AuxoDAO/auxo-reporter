# read the compounding file and ensure totals add correctly

import json

EPOCH = "2023-6"
COMPOUND_EPOCH = "0"


def main():
    with open(f"reports/{EPOCH}/compounding/compound-ARV-{COMPOUND_EPOCH}.json") as f:
        ARV = json.load(f)

    with open(f"reports/{EPOCH}/compounding/compound-PRV-{COMPOUND_EPOCH}.json") as f:
        PRV = json.load(f)

    # fetch totals from json
    for (name, token) in [("ARV", ARV), ("PRV", PRV)]:
        summed = sum(
            int(recipient["rewards"]["amount"]) for recipient in token["recipients"]
        )
        total = int(token["amount"])
        diff = summed - total
        if diff <= 0:
            emoji = "✅"
        else:
            emoji = "❌"
        print(f"{name} summed: {summed} | total: {total} | diff: {diff} {emoji} ")


if __name__ == "__main__":
    main()
