# Auxo-Reporter

The Auxo reporter is used to create MerkleTrees for the Auxo protocol.
It fetches data from The Graph, Snapshot and Directly from the blockchain, then calculates the rewards for each user and generates a MerkleTree of claims that can be uploaded on chain.

## Structure

```sh
Makefile        # set of pre-defined scripts to get you started

# Python files
reporter/        # Python application to parse config data into rewards database
  models/        # Classes and class behaviours
  queries/       # on chain and subgraph queries
  rewards/       # Reward calculations
  test/          # Unit tests
  run.py         # Main script to run the reporter
  *.py           # other misc python files needed for the app
reports/         # Output files relating to claims, voting, proposals, rewards and the final tree
config/          # Config files for the reporter
pyproject.toml   # Python tooling setup
requirements.txt # Python dependencies

# Typescript files
merkleTree/     # Typescript MerkleTree generator with OpenZeppelin
package.json    # NodeJS dependencies and scripts
tsconfig.json   # Typescript config
```

## Installation

Make sure you have Python, Pip, NodeJS, Yarn installed. Python 3.10+ is recommended.

The [Makefile](./Makefile) contains a set of scripts to get you started. Provided you have `make` installed:

Setup the python venv and activate:

```sh
make venv
source venv/bin/activate
```

Install everything :

```sh
make setup
```

Check for type errors and format everything:

```sh
make lint
```

Run unit tests

```sh
make test
```

> An E2E test gets run and will write to the `reports` folder in the year 2099. Feel free to delete this.

## Running the Application

### Setting up the `.env`:

The [example env](.env.example) file requires you to grab a number of contract addresses, subgraph endpoints and API keys. This needs only doing once and a lot of these are pre-populated for you.

### Running each epoch

Provided the env is configured, everything else is built from a config file, you can find full details by reading the [example file](./config/example.jsonc).

You can autogenerate a config file from the example with:

```sh
make conf
```

This will create a `config/example.json` file with some example data and the schema incorporated. The schema provides some basic warnings and validations to help you get started but it is not essential.

Create the database of claims and rewards:

```sh
# You will be promoted to provide the path to your config file.
make claims
```

If all goes well, you should have a new folder `reports/{year}-{month}/`, i.e. `reports/2022-11/`. Where {year} and {month} are the year and month as defined in your config file.

In it you will have the following files:

```sh
csv/                  # Report data in CSV format
json/                 # Report data in JSON format
claims.json           # Rewards by ethereum address, nil for inactive/slashed users
epoch-conf.json       # autogenerated config file based on your input config file
reporter-db.json      # Full breakdown of all generated data. Can be readable by TinyDB
```

You can then generate the merkle tree file with:

```sh
make tree
```

This will output a `merkle-tree.json` file in the reports folder for your passed epoch.

You will be asked whether to post to IPFS. If you want to do this, you will need to follow the instructions below before building the merkle tree.

## Posting to IPFS

You can use [Web3.storage](https://web3.storage/tokens/) to create an API Key.

Add it to a `.env` file by copying the `.env.example` and adding your key.

That's it! Just follow the instructions in the command prompt and you will automatically post to the IPFS and generate a link.

## Compounding

Compounding refers to users delegating their claim back to the DAO, in exchange for more Auxo. 

> At the time of writing, Delegated rewards are converted to PRV only.

Steps for compounding:

1. User must delegate claim to the Multisig
2. Fetch claims for delegated users
3. Treasury can claim on behalf of delegated users, WETH is sent to the treasury
4. WETH is used to purchase Auxo
5. Based on the number of Auxo purchased, a pro-rata figure for WETH is computed
6. Users are sent (pro-rata * WETH_qty) PRV

### Notes on compounding

There are a few ways to fetch the compounding data:

1. Event logs: we can fetch the list of Delegated Events from the contract
    - DelegateAdded with the MULTISIG would be good
    - We also need to track DelegateRemoved
    - You would probably still need to check the user's claims are still valid
2. Contract Calls: we can reach out to the contract at a specific block to get a few bits of data:
    - run `isRewardsDelegate(MULTISIG, user)` for all users in the claims window
    - run `isClaimed(accountIndex, windowIndex)` for all delegated accounts
   This gives us users who have yet to claim, but have delegated.

(1) is probably best handled using a subgraph to maintain a current `state` of delegation
Both (1) and (2) have the potential problem that it is still possible to claim while delegated. 
From a process POV you probably need to lock the Distributor before doing the compounding

Next, we need to create a batch TX to claim for all users. This simply involves filtering the merkle tree for all users who are delegated and !claimed.

Once claimed the contracts can be unlocked.

The DAO will have a total WETH value and a WETH value per user. This should be saved in a snapshot.

We can finally compute a pro-rata WETH:Auxo/PRV value per user by inputting the total Auxo back into the reporter.





