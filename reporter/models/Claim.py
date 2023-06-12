from typing import Union

from pydantic import BaseModel

from reporter.models.Reward import ARVRewardSummary, PRVRewardSummary
from reporter.models.types import BigNumber, Bytes32, EthereumAddress


#   struct Claim {
#       uint256 windowIndex;
#       uint256 accountIndex;
#       uint256 amount;
#       address token;
#       bytes32[] merkleProof;
#       address account;
#   }
Claim = tuple[int, int, BigNumber, EthereumAddress, list[Bytes32], EthereumAddress]


class ClaimsRecipient(BaseModel):
    """
    Minimal claim data for each recipient that will be used to generate the merkle tree
    :param `windowIndex`: distribution index, should be unique
    :param `accountIndex`: autoincrementing but unique index of claim within a window.
    Used by the MerkleDistributor to efficiently index on-chain claiming.
    """

    windowIndex: int
    accountIndex: int
    rewards: BigNumber
    token: EthereumAddress


class ClaimsWindow(BaseModel):
    """
    The full claim data used to generate the tree. The tree doesn't use anything other than
    the recipients data, so the additional metadata in `aggregateRewards` is purely for readability.
    """

    windowIndex: int
    chainId: int
    aggregateRewards: Union[ARVRewardSummary, PRVRewardSummary]
    recipients: dict[EthereumAddress, ClaimsRecipient]


class MerkleRecipient(ClaimsRecipient):
    """
    Extend the base ClaimsRecipient with a MerkleProof

    """

    proof: list[Bytes32]


RecipientMerkleClaim = dict[EthereumAddress, MerkleRecipient]


class MerkleTree(ClaimsWindow):
    """
    Extends the base ClaimsWindow with a root hash and Merkl Recipients

    """

    windowIndex: int
    chainId: int
    aggregateRewards: Union[ARVRewardSummary, PRVRewardSummary]
    recipients: RecipientMerkleClaim
    root: Bytes32
