import json
from reporter.models.types import BigNumber, EthereumAddress

TREE_PATH = 'reporter/test/stubs/compound'


COMPOUNDERS: list[tuple[EthereumAddress, BigNumber]] = [
    ("0x89d2D4934ee4F1f579056418e6aeb136Ee919d65", "2498026159571371249"),
    ("0x4281579D99d855F2430C95a13720e53a0fCC0549", "2324861546384188872"),
    ("0xFbEA6F2B10e8Ee770F37Fff9B8C9E10d9B65741D", "911557936721782185"),
    ("0x56446712B219fcC34a5604f5E7AF5d50d65B6647", "901691975068800020"),
    ("0x461F635488972409981EDbD043834dbaA7239FA6", "670072988829689815"),
    ("0x519A0dF0Bd2b586b6F7126799c30A243E13ABCbe", "557672023131008100"),
    ("0x7bDb45b1fe5B3eB17a4C7a16C9750C7e10CcF08d", "566352308742886738"),
    ("0x1754352eacb753327Fec2d4F48f0fb36B672C5e0", "452267924176500487"),
    ("0xd3C808920D8fCcBeBd181Aae8D4FB2ACd1A433cD", "445677354819216746"),
    ("0x16765c8Fe6Eb838CB8f64e425b6DcCab38D4F102", "422220549747025535"),
    ("0x1dE4F046c45Cd4E39cfCDF36b7DF4856B4031955", "435669462495420024"),
    ("0x7ccf173012bfE53F16F4D6A2a4aea32abAfcD04C", "412379699001591308"),
    ("0xF8C84C6A4f1083f7a7Fd94885B303A3974116D82", "416807378697823601"),
    ("0x5C7a20b1EFa9A2aB5F448b651Aa264F233076C4C", "358944883096733627"),
    ("0x00BA3CA0B6Df1486c912893d9f288311A60ED753", "277601719079812013"),
    ("0xD9A0013af48591f8524280D6f8f98189cef45308", "286960742053179489"),
]

NON_COMPOUNDOORS = [
        "0xC9EF3A5f54d1122898fc36AC4d25AD5DC40ad620",
        "0x9fa203C0526b71acD52699E6C16744cD5873B09D",
        "0xB70B56B84b76c823D35b72D5566f5C341Ed13ad2",
        "0x59Ba43462ea618c39429B38F5A75cd87D9F0B2b8",
        "0xB8daA7986A3862b974177eb6eF3bbf0211F858D1",
        "0xCafF1dac2eD451a0C9F61e6445175048974E35a7",
        "0x559032700A79af643A149DF1432dB284C48E524b",
        "0x7024D6F89C2ADF88904812728cA68730eABBA23D",
        "0x9cB55DC24641511FD586Dbf25067799F845C2C19",
    ]

CLAIMOOORS = [
    "0x578104a30B5dF2c7092Ec5F66A6766be4E6Baa3e",
    "0xdA74CdeE06b9e1067F8664129A61B10CADAA6c18",
    "0xC7af166691A06E217B08935FBE6C5Fc5D03751f6",
    "0x7716c88b632458Ab62aE0E78cFAa3e9C2a30a73D",
    "0x999781A4b98010a497c13385C7437551520A1278",
    "0x2242618f1272e52C9930720e0d1B47D258175aaa",
    "0x5D11669C9fA09A78190AD255377BBd932432dD86",
    "0x43AcEd99D1BF6da686E84b6D7B9b4950B58919fE",
    "0xb342De8c16E418dD5Aad9dB22e70922F72759553",
    "0xF9efabefB7954Eeee036a8C36a70D7fAeD734B29",
    "0x63ccE2078fa0717f7CBa49580D3b91783Efebd1A",
]


def create_is_claimed_response() -> dict[EthereumAddress, bool]:
    res = {}

    for address, _ in COMPOUNDERS:
        res[address] = False

    for address in NON_COMPOUNDOORS:
        res[address] = False

    for address in CLAIMOOORS:
        res[address] = True

    return res

def create_is_compounder_response() -> dict[EthereumAddress, bool]:
    res = {}

    for address, _ in COMPOUNDERS:
        res[address] = True

    for address in CLAIMOOORS:
        res[address] = True

    for address in NON_COMPOUNDOORS:
        res[address] = False

    return res

def create_mock_tree():
    # read the source merkle tree
    with open(f'{TREE_PATH}/original/merkle-tree-ARV.json') as f:
        tree = json.load(f)

    # save recipients and clear out - we will be replacing them
    recipient_data = list(tree['recipients'].values())
    tree['recipients'] = {}

    # replace the first len(COMPOUNDERS) recipients with the COMPOUNDERS addresses and rewards
    for i, (address, reward) in enumerate(COMPOUNDERS):
        tree['recipients'][address] = recipient_data[i]
        tree['recipients'][address]['reward'] = reward
        
    # replace the next len(NON_COMPOUNDOORS) recipients with the NON_COMPOUNDOORS addresses
    for i, address in enumerate(NON_COMPOUNDOORS):
        tree['recipients'][address] = recipient_data[i + len(COMPOUNDERS)] 

    # replace the next len(CLAIMOOORS) recipients with the CLAIMOOORS addresses
    for i, address in enumerate(CLAIMOOORS):
        tree['recipients'][address] = recipient_data[i + len(COMPOUNDERS) + len(NON_COMPOUNDOORS)]

    assert len(tree['recipients']) == len(COMPOUNDERS) + len(NON_COMPOUNDOORS) + len(CLAIMOOORS)

    # save our new tree
    with open(f'{TREE_PATH}/merkle-tree-ARV.json', 'w') as f:
        json.dump(tree, f, indent=2)
