import { readFileSync, writeFileSync } from "fs";
import { createWithdrawalsTree } from "./create";
import axios from "axios";
import * as dotenv from "dotenv";

dotenv.config();
const { stdin, stdout } = process;
const ENDPOINT =
  "https://api.thegraph.com/subgraphs/name/jordaniza/auxo-staking";

async function queryPRVNonZeroBalancesAtBlock(
  blockNumber: number
): Promise<GraphQLResponse<ERC20GraphQLResponse>> {
  const query = `
  query PRVNonZeroBalancesAtBlock {
    erc20Balances(
      block: {number: ${blockNumber}},
      where: {
        and: [
          {contract_: {symbol: "PRV"}},
          {value_not: "0"},
          {account_not: null}
        ]
      }
    ) {
      account {
        id
      }
      value
      valueExact
    }
  }
`;

  try {
    const response = await axios.post(ENDPOINT, { query });
    return response.data;
  } catch (error) {
    console.error(error);
    throw new Error("No response from the Subgraph");
  }
}

/**
 * Grabs PRV staking positions from the Subgraph
 */
async function fetchPRVHolders(
  blockNumber: number,
  windowIndex: number
): Promise<WithdrawalDistributorInput> {
  const response = await queryPRVNonZeroBalancesAtBlock(blockNumber);
  const { erc20Balances } = response.data;
  const recipients: WithdrawalRecipient = {};
  erc20Balances.forEach((balance) => {
    recipients[balance.account.id] = {
      windowIndex,
      amount: balance.valueExact,
    };
  });

  return {
    windowIndex,
    maxAmount: "0",
    startBlock: blockNumber,
    endBlock: blockNumber,
    recipients,
  };
}

function prompt(question: string) {
  return new Promise((resolve, reject) => {
    stdin.resume();
    stdout.write(question);

    stdin.on("data", (data) => resolve(data.toString().trim()));
    stdin.on("error", (err) => reject(err));
  });
}

const destination = (epoch: unknown) =>
  `reports/${epoch}/merkle-verifier-PRV.json`;

export const makeTreeWithPrompt = async ({
  epoch,
  blockNumber,
  windowIndex,
  startBlock,
  endBlock,
  budget,
  isDryRun = true,
}: {
  epoch: unknown;
  windowIndex: number;
  startBlock: number;
  endBlock: number;
  budget: string;
  blockNumber: number;
  isDryRun?: boolean;
}) => {
  const holders = await fetchPRVHolders(blockNumber, windowIndex);

  // create the tree as a string
  const tree = JSON.stringify(
    createWithdrawalsTree(holders, {
      windowIndex,
      startBlock,
      endBlock,
      maxAmount: budget,
    }),
    null,
    4
  );

  // write the file
  const fileDestination = destination(epoch);
  if (!isDryRun) writeFileSync(fileDestination, tree);
  console.log(tree);
  console.log(fileDestination);
  console.log(
    `✨✨ Withdrawal Merkle Verifier Created at ${fileDestination} ✨✨`
  );
};

async function main() {
  const epoch = await prompt("What is the epoch {YYYY}-{MM}? eg: 2022-11\n");
  const blockNumberPrompt = await prompt("What is the block number?\n");
  const blockNumber = parseInt(blockNumberPrompt as string);
  let input = await prompt(
    "WindowIndex, budget (in wei), startBlock, and endBlock, separated by spaces:\n"
  );
  let inputs = (input as string).split(" ").map((i) => i.trim());
  if (inputs.length !== 4) {
    throw new Error("Incorrect number of inputs");
  }
  const writeFile = await prompt(
    "Do you want to write the merkleTree file? (y/n)\n"
  );
  const isDryRun = writeFile === "n";
  let [_windowIndex, budget, _startBlock, _endBlock] = inputs;

  await makeTreeWithPrompt({
    epoch,
    windowIndex: parseInt(_windowIndex),
    startBlock: parseInt(_startBlock),
    endBlock: parseInt(_endBlock),
    budget,
    blockNumber,
    isDryRun,
  });
}

// only run if called directly
if (require.main === module)
  main()
    .catch(console.error)
    .finally(() => process.exit(0));
