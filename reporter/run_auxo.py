from decimal import getcontext
from reporter.queries.all_holders import get_all_auxo_holders

# set the context for decimal precision to avoid scientific notation
getcontext().prec = 42


if __name__ == "__main__":
    get_all_auxo_holders()
