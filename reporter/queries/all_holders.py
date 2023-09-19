import requests
from reporter.queries import get_token_hodlers
from reporter.config import load_conf
from reporter.queries import (
    get_all_prv_depositors,
    get_arv_stakers,
    graphql_iterate_query,
    extract_nested_graphql,
)
from env import ADDRESSES, SUBGRAPHS
from copy import deepcopy
from typing import Any, TypedDict, TypeVar, cast

import requests
from decimal import Decimal, getcontext
from web3 import Web3
import json, csv

from reporter.env import RPC_URL, SUBGRAPHS
from reporter.errors import EmptyQueryError, TooManyLoopsError
from reporter.models import GraphQL_Response, Config, EthereumAddress

getcontext().prec = 42


def get_all_arv_depositors(block: int):
    """
    returns a simple list of every user that has a nonzero PRV staked balance in the rollstaker.
    This will include pending stakes that should not be counted as active

    Therefore, ensure you check the user's active balance (in the current epoch) before assigning rewards.
    """
    query = """
    query ARVLockHistory ($block: Int) {
      tokenLockerContract(
        block: {number: $block},
        id: "0x3E70FF09C8f53294FFd389a7fcF7276CC3d92e64"
      )  {
        locks{
          account {
            id
          }
          auxoValue
          auxoValueExact
          arvValue
          arvValueExact
        }
      }
    }   
    """
    url = SUBGRAPHS.AUXO_STAKING
    response: GraphQL_Response = requests.post(
        url, json=dict(variables={"block": block}, query=query)
    ).json()

    if not response:
        raise EmptyQueryError(f"No results for graph query to {url}")
    if "errors" in response:
        raise EmptyQueryError(
            f"Error in graph query to {url}: {cast(dict, response)['errors']}"
        )

    return extract_nested_graphql(response, ["tokenLockerContract", "locks"])


EXCLUDE_LIST = [
    "0x3e70ff09c8f53294ffd389a7fcf7276cc3d92e64",  # token locker
    "0xc72fbd264b40d88e445bcf82663d63ff21e722af",  # prv
    "0x096b4f2253a430f33edc9b8e6a8e1d2fb4faa317",  # rollstaker
    "0x0000000000000000000000000000000000000000",  # null address
    "0x000000000000000000000000000000000000dead",  # dead address
    "0x3bCF3Db69897125Aa61496Fc8a8B55A5e3f245d5",  # treasury
]


def get_all_auxo_holders(
    exclude=EXCLUDE_LIST,
):
    conf = load_conf("reports/dissolution")

    auxo = get_token_hodlers(conf, ADDRESSES.AUXO)
    prv = get_token_hodlers(conf, ADDRESSES.PRV)
    prv_staker = get_all_prv_depositors(conf.block_snapshot)
    arv_locked = get_all_arv_depositors(conf.block_snapshot)

    # create a list by ETH address

    # first destructure the auxo list

    total = {}

    for a in auxo:
        address = a["account"]["id"].lower()
        total[address] = {
            "auxo": a["valueExact"],
        }

    for p in prv:
        address = p["account"]["id"].lower()
        if address in total:
            total[address]["prv"] = p["valueExact"]
        else:
            total[address] = {
                "prv": p["valueExact"],
            }

    for p in prv_staker:
        address = p["account"]["id"].lower()
        if address in total:
            total[address]["prv_staker"] = p["valueExact"]
        else:
            total[address] = {
                "prv_staker": p["valueExact"],
            }

    for a in arv_locked:
        address = a["account"]["id"].lower()
        if address in total:
            total[address]["arv_locked"] = a["auxoValueExact"]
        else:
            total[address] = {
                "arv_locked": a["auxoValueExact"],
            }

    # compute totals
    for k, v in total.items():
        if "prv" not in v:
            v["prv"] = 0
        if "prv_staker" not in v:
            v["prv_staker"] = 0
        if "arv_locked" not in v:
            v["arv_locked"] = 0
        if "auxo" not in v:
            v["auxo"] = 0

    # remove exclude list
    for e in exclude:
        lower_e = e.lower()
        if lower_e in total:
            del total[lower_e]

    # compute total
    global_total = 0
    for k, v in total.items():
        user_total = (
            int(v["prv"]) + int(v["prv_staker"]) + int(v["arv_locked"]) + int(v["auxo"])
        )
        v["total"] = user_total
        global_total += user_total

    pro_rata = str(Decimal(conf.rewards.amount) / Decimal(global_total))

    # now get everyone's share as a percentage
    for k, v in total.items():
        share = Decimal(v["total"]) / Decimal(global_total)
        reward_share = share * Decimal(conf.rewards.amount)
        v["share"] = str(share)
        v["reward_share"] = str(int(reward_share))

    with open("reports/dissolution/auxo_holders.json", "w") as f:
        json.dump(total, f)

    with open("reports/dissolution/auxo_holders.csv", "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(
            [
                "address",
                "auxo",
                "prv",
                "prv_staker",
                "arv_locked",
                "total",
                "share",
                "reward_share",
            ]
        )
        for k, v in total.items():
            csv_writer.writerow(
                [
                    k,
                    v["auxo"],
                    v["prv"],
                    v["prv_staker"],
                    v["arv_locked"],
                    v["total"],
                    v["share"],
                    v["reward_share"],
                ]
            )

    # write claims
    with open("reports/dissolution/auxo_claims.json", "w") as f:
        claims = {}
        claims["window_index"] = conf.distribution_window
        claims["chainId"] = 1
        claims["aggregateRewards"] = conf.rewards.dict()
        claims["aggregateRewards"]["pro_rata"] = str(pro_rata)
        claims["recipients"] = {}

        for idx, (k, v) in enumerate(total.items()):
            claims["recipients"][k] = {
                "windowIndex": conf.distribution_window,
                "accountIndex": idx,
                "rewards": v["reward_share"],
                "token": conf.rewards.address,
            }

        json.dump(claims, f)
