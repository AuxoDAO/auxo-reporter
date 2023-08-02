from typing import Any
from pydantic import parse_obj_as
import reporter.utils as utils
from reporter.env import ADDRESSES, SNAPSHOT_SPACE_ID
from reporter.models import (
    Config,
    Delegate,
    Vote,
    Proposal,
    OnChainProposal,
    OnChainVote,
    ARVStaker,
)
from reporter.queries.common import SUBGRAPHS, graphql_iterate_query


def get_offchain_votes(conf: Config):
    """Fetch snapshot votes for the DAO between start and end timestamps in config object"""

    votes_query = """
        query($skip: Int, $space: String, $created_gte: Int, $created_lte: Int) { 
            votes(skip: $skip, first: 1000, where: {space: $space, created_gte: $created_gte, created_lte: $created_lte}) {
                voter
                choice
                created
                proposal {
                    id
                    title
                    author
                    created
                    start
                    end
                    choices
                }
            }
        }
    """

    variables = {
        "skip": 0,
        "space": SNAPSHOT_SPACE_ID,
        "created_gte": conf.start_timestamp,
        "created_lte": conf.end_timestamp,
    }

    votes: list[Any] = graphql_iterate_query(
        SUBGRAPHS.SNAPSHOT, ["votes"], dict(query=votes_query, variables=variables)
    )
    return votes


def get_onchain_votes(conf: Config) -> list:
    """
    Grab vote proposals and votes from OZ Governor
    To check: does the OZ implementation check delegation?
    """

    votes_query = """
    query($governor: String, $timestamp_gt: Int, $timestamp_lte: Int, $skip: Int) {
        voteCasts(
            first: 1000
            skip: $skip
            where: { 
                timestamp_gt: $timestamp_gt,
                timestamp_lte: $timestamp_lte,
                governor: $governor
            }
        ) {
            id
            receipt {
                reason
            }
            support {
                support
            }
            proposal {
                description
                canceled
                executed
                id
                endBlock
                startBlock
                proposer {
                    id
                }
                proposalCreated {
                    timestamp
                }
            }
            governor {
                id
            }
            voter {
                id
            }
            timestamp
        }     
    }
    """

    variables = {
        "skip": 0,
        "governor": ADDRESSES.GOVERNOR,
        "timestamp_gt": conf.start_timestamp,
        "timestamp_lte": conf.end_timestamp,
    }
    votes: list[Any] = graphql_iterate_query(
        SUBGRAPHS.AUXO_GOV,
        ["voteCasts"],
        dict(query=votes_query, variables=variables),
    )
    return votes


def filter_votes_by_proposal(
    votes: list[Vote],
) -> tuple[list[Vote], list[Proposal]]:
    """
    Prompt the operator to remove invalid proposals this month
    :param `votes`: list of all votes
    :returns: A tuple of valid votes and proposals
    """

    unique_proposals = {v.proposal.id: v.proposal for v in votes}
    if utils.yes_or_no("Do you want to filter proposals?"):
        proposals = []
        proposals_ids = []
        for p in unique_proposals.values():

            if utils.yes_or_no(f"Is proposal {p.title} a valid proposal?"):
                proposals.append(p)
                proposals_ids.append(p.id)

        return ([v for v in votes if v.proposal.id in proposals_ids], proposals)

    else:
        return (votes, list(unique_proposals.values()))


def get_delegates() -> list[Delegate]:
    """
    We only have 1 whitelisted delegate at the moment, so easiest just to hardcode it
    """
    return [
        Delegate(
            delegator="0x4D04EB67A2D1e01c71FAd0366E0C200207A75487",
            delegate="0xEa9f2E31Ad16636f4e1AF0012dB569900401248a",
        )
    ]


def get_voters(
    votes: list[Vote], stakers: list[ARVStaker]
) -> tuple[list[str], list[str]]:
    """
    Compare the list of `stakers` to the list of `votes` to see who has/has not voted this month.
    Also factors in delegated votes for whitelisted accounts.
    :returns: 2 lists:
        * First is all addresses that voted
        * Second is all addresses that have not voted

    dev: in the first epoch, we did not require voting, everyone was counted as active
    the code below was replaced with:
    ```
    voted = [addr for addr in stakers_addrs_no_delegators]
    not_voted = []
    ```
    """
    voters = set([v.voter for v in votes])
    stakers_addrs = [s.address for s in stakers]

    # TODO: Delegation is not currently supported
    delegates = get_delegates()

    stakers_addrs_no_delegators = [
        addr for addr in stakers_addrs if addr not in delegates
    ]

    voted = [addr for addr in stakers_addrs_no_delegators if addr in voters] + [
        d.delegator for d in delegates if d.delegate in voters
    ]

    not_voted = [addr for addr in stakers_addrs_no_delegators if addr not in voters] + [
        d.delegator for d in delegates if d.delegate not in voters
    ]

    return (utils.unique(voted), utils.unique(not_voted))


def parse_offchain_votes(conf: Config) -> list[Vote]:
    return parse_obj_as(list[Vote], get_offchain_votes(conf))


def parse_onchain_votes(conf: Config) -> list[OnChainVote]:
    return parse_obj_as(list[OnChainVote], get_onchain_votes(conf))


def combine_on_off_chain_proposals(
    offchain: list[Proposal], onchain: list[OnChainProposal]
) -> list[Proposal]:

    coerced = [ocp.coerce_to_proposal() for ocp in onchain]
    return offchain + coerced


def combine_on_off_chain_votes(
    offchain: list[Vote], onchain: list[OnChainVote]
) -> list[Vote]:

    coerced = [ocv.coerce_to_vote() for ocv in onchain]
    return offchain + coerced


def get_votes(conf: Config) -> tuple[list[Vote], list[Proposal]]:
    """
    Fetch all votes from offchain and onchain sources and combine them
    """
    offchain_votes = parse_offchain_votes(conf)
    onchain_votes = parse_onchain_votes(conf)

    combined_votes = combine_on_off_chain_votes(offchain_votes, onchain_votes)

    return filter_votes_by_proposal(combined_votes)
