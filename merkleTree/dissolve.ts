import { readFileSync, writeFile, writeFileSync } from "fs";
import { createMerkleTree } from "./create";
import { validateTree } from "./validate";
import { BigNumber, FixedNumber } from "ethers";

type DissolutionTree = {
  [address: `0x${string}`]: {
    [claimIndex: number]: MerkleDistributor["recipients"][number];
  };
};

function main() {
  const claims = JSON.parse(
    readFileSync(`reports/dissolution/auxo_claims.json`, {
      encoding: "utf8",
    })
  );

  const tree = createMerkleTree(claims);
  const secondTree = createMerkleTree(createMockClaims(claims));

  if (!validateTree(tree)) throw new Error("Invalid tree");

  const strTree = JSON.stringify(tree, null, 4);
  writeFileSync(`reports/dissolution/merkle-tree.json`, strTree);
  console.log(`✨✨ Merkle Tree Created at reports/dissolution/merkle-tree.json ✨✨`);

  const strSecondTree = JSON.stringify(secondTree, null, 4);
  writeFileSync(`reports/dissolution/merkle-tree-mock.json`, strSecondTree);
  console.log(`✨✨ Merkle Tree Created at reports/dissolution/merkle-tree-mock.json ✨✨`);

  const dissolutionTree: DissolutionTree = {};
  Object.keys(tree.recipients).forEach((address) => {
    dissolutionTree[address as `0x${string}`] = {};
    dissolutionTree[address as `0x${string}`][0] = tree.recipients[address];
    dissolutionTree[address as `0x${string}`][1] = secondTree.recipients[address];
  });

  // write it to a file
  const strDissolutionTree = JSON.stringify(dissolutionTree, null, 4);
  writeFileSync(`reports/dissolution/dissolution-tree.json`, strDissolutionTree);
  console.log(`✨✨ Dissolution Tree Created at reports/dissolution/dissolution-tree.json ✨✨`);
}

if (require.main === module) {
  main();
}

function createMockClaims(existingClaims: MerkleDistributorInput): MerkleDistributorInput {
  // divide each claim by 10 and add 1 to the window index
  const mockClaims = Object.entries(existingClaims.recipients).reduce((prev, [address, claim]) => {
    const mockClaim = {
      ...claim,
      windowIndex: claim.windowIndex + 1,
      rewards: BigNumber.from(claim.rewards).div(10).toString(),
    };
    return { ...prev, [address]: mockClaim };
  }, {});

  return {
    ...existingClaims,
    windowIndex: existingClaims.windowIndex + 1,
    aggregateRewards: {
      ...existingClaims.aggregateRewards,
      amount: BigNumber.from(existingClaims.aggregateRewards.amount).div(10).toString(),
      pro_rata: (Number(existingClaims.aggregateRewards.pro_rata) / 10).toString(),
    },
    recipients: mockClaims,
  };
}
