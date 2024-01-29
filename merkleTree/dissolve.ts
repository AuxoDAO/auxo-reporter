import { readFileSync, writeFile, writeFileSync } from "fs";
import { createMerkleTree } from "./create";
import { validateTree } from "./validate";

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
  console.log(`✨✨ Merkle Tree Created at reports/${DISSOLUTION_DIR}/merkle-tree.json ✨✨`);

  const dissolutionTree: DissolutionTree = {};
  Object.entries(tree.recipients).forEach(([address, claim]) => {
    dissolutionTree[address as `0x${string}`] = {};
    dissolutionTree[address as `0x${string}`][0] = tree.recipients[address];
  });

  // write it to a file
  const strDissolutionTree = JSON.stringify(dissolutionTree, null, 4);
  writeFileSync(`reports/${DISSOLUTION_DIR}/dissolution-tree.json`, strDissolutionTree);
  console.log(`✨✨ Dissolution Tree Created at reports/${DISSOLUTION_DIR}/dissolution-tree.json ✨✨`);
}

if (require.main === module) {
  main();
}
