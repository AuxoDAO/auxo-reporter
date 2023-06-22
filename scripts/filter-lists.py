import json

EPOCH = '2023-6'
COMPOUND_EPOCH = '0'

def main():
    with open(f'reports/{EPOCH}/compounding/recipients-ARV-{COMPOUND_EPOCH}.json') as f:
        ARV = json.load(f)

    with open(f'reports/{EPOCH}/compounding/recipients-PRV-{COMPOUND_EPOCH}.json') as f:
        PRV = json.load(f)

    all_addresses = []
    # fetch totals from json
    for (name, token) in [('ARV', ARV), ('PRV',PRV)]:
        addresses = token.keys()
        all_addresses += addresses


    all_addresses = list(set(all_addresses))
    __import__('pprint').pprint(all_addresses)

if __name__ == '__main__':
    main()
