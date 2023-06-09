from reporter.env import ADDRESSES
from reporter.queries import w3
from multicall import Call, Multicall  # type: ignore
from reporter.models import MerkleRecipient, MerkleTree, RecipientMerkleClaim, EthereumAddress


MulticallIsRewardsCompounder = dict[EthereumAddress, bool]


def multicall_is_compounder(
    recipients: RecipientMerkleClaim,
    distributor: EthereumAddress,
    block_number: int,
) -> MulticallIsRewardsCompounder:

    calls = [
        Call(
            # address to call:
            distributor,
            # function isRewardsDelegate(address _user, address _delegate) public view returns (bool)
            ["isRewardsDelegate(address,address)(bool)", address, ADDRESSES.MULTISIG_OPS],
            # return in a format of {[address]: bool}:
            [[address, None]],
        )
        for address in recipients.keys()
    ]

    # Immediately execute the multicall
    return Multicall(calls, _w3=w3, block_id=block_number)()


MulticallIsRewardsClaimed = dict[EthereumAddress, bool]


def multicall_is_claimed(
    recipients: RecipientMerkleClaim,
    distributor: EthereumAddress,
    block_number: int,
) -> MulticallIsRewardsCompounder:

    calls = [
        Call(
            # address to call:
            distributor,
            # function isClaimed(uint256 _windowIndex, uint256 _accountIndex) public view returns (bool) {
            [
                "isClaimed(uint256,uint256)(bool)",
                recipient.windowIndex,
                recipient.accountIndex,
            ],
            # return in a format of {[address]: bool}:
            [[address, None]],
        )
        for address, recipient in recipients.items()
    ]

    # Immediately execute the multicall
    return Multicall(calls, _w3=w3, block_id=block_number)()


def delegated_and_unclaimed(
    delegated: MulticallIsRewardsCompounder, claimed: MulticallIsRewardsClaimed
) -> list[EthereumAddress]:
    return [
        address
        for address, is_delegated in delegated.items()
        if is_delegated and not claimed[address]
    ]


def get_unclaimed_delegated_recipients(
    tree: MerkleTree, distributor: EthereumAddress, block: int
) -> RecipientMerkleClaim:
    delegated = multicall_is_compounder(tree.recipients, distributor, block)
    claimed = multicall_is_claimed(tree.recipients, distributor, block)
    delegated_but_unclaimed = delegated_and_unclaimed(delegated, claimed)
    return {
        recipient: MerkleRecipient.parse_obj(tree.recipients[recipient])
        for recipient in delegated_but_unclaimed
    }
