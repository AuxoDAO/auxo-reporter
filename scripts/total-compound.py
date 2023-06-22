# read the compounding file and get totals

import json


EPOCH = '2023-6'
COMPOUND_EPOCH = '0'


def main():
    with open(f'reports/{EPOCH}/compounding/recipients-ARV-{COMPOUND_EPOCH}.json') as f:
        ARV = json.load(f)

    with open(f'reports/{EPOCH}/compounding/recipients-PRV-{COMPOUND_EPOCH}.json') as f:
        PRV = json.load(f)


    # fetch totals from json
    for (name, token) in [('ARV', ARV), ('PRV',PRV)]:
        compounders = len(token.values())
        total = sum(int(user['rewards']) for user in token.values())
        print(f'Group: {name}, Compounded Rewards: {total}, {total/1e18} across {compounders} compounders')

if __name__ == '__main__':
    main()
