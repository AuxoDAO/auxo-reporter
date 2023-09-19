import { readFileSync, writeFile, writeFileSync } from "fs";
import { createMerkleTree } from "./create";
import { validateTree } from "./validate";

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

  if (!validateTree(tree)) throw new Error("Invalid tree");

  const strTree = JSON.stringify(tree, null, 4);
  writeFileSync(`reports/dissolution/merkle-tree.json`, strTree);
  console.log(`✨✨ Merkle Tree Created at reports/dissolution/merkle-tree.json ✨✨`);

  const dissolutionTree: DissolutionTree = {};
  Object.entries(tree.recipients).forEach(([address, claim]) => {
    dissolutionTree[address as `0x${string}`] = {};
    dissolutionTree[address as `0x${string}`][0] = tree.recipients[address];
  });

  // write it to a file
  const strDissolutionTree = JSON.stringify(dissolutionTree, null, 4);
  writeFileSync(`reports/dissolution/dissolution-tree.json`, strDissolutionTree);
  console.log(`✨✨ Dissolution Tree Created at reports/dissolution/dissolution-tree.json ✨✨`);
}

if (require.main === module) {
  main();
}
