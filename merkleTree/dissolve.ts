import { readFileSync, writeFileSync } from "fs";
import { createMerkleTree } from "./create";
import { validateTree } from "./validate";

const PREV_DISSOLUTION_DIR = "dissolution";
const DISSOLUTION_DIR = "dissolution-2";

type DissolutionTree = {
  [address: `0x${string}`]: {
    [claimIndex: number]: MerkleDistributor["recipients"][number];
  };
};

function main() {
  const claims = JSON.parse(
    readFileSync(`reports/${DISSOLUTION_DIR}/auxo_claims.json`, {
      encoding: "utf8",
    })
  );

  const tree = createMerkleTree(claims);

  if (!validateTree(tree)) throw new Error("Invalid tree");

  const strTree = JSON.stringify(tree, null, 4);
  writeFileSync(`reports/${DISSOLUTION_DIR}/merkle-tree.json`, strTree);
  console.log(
    `✨✨ Merkle Tree Created at reports/${DISSOLUTION_DIR}/merkle-tree.json ✨✨`
  );

  // get the previous dissolution tree as a starting point
  const dissolutionTree = JSON.parse(
    readFileSync(`reports/${PREV_DISSOLUTION_DIR}/dissolution-tree.json`, {
      encoding: "utf8",
    })
  ) as DissolutionTree;

  Object.entries(tree.recipients).forEach(([address, claim]) => {
    if (!dissolutionTree[address as `0x${string}`]) {
      throw new Error(
        `Address ${address} not found in previous dissolution tree`
      );
    } else {
      dissolutionTree[address as `0x${string}`][1] = tree.recipients[address];
    }
  });

  // write it to a file
  const strDissolutionTree = JSON.stringify(dissolutionTree, null, 4);
  writeFileSync(
    `reports/${DISSOLUTION_DIR}/dissolution-tree.json`,
    strDissolutionTree
  );
  console.log(
    `✨✨ Dissolution Tree Created at reports/${DISSOLUTION_DIR}/dissolution-tree.json ✨✨`
  );
}

if (import.meta.main) {
  main();
}
