from reporter.config import main as config
from reporter.run_prv import run_prv
from reporter.run_arv import run_arv


if __name__ == "__main__":
    epoch = config()
    run_arv(epoch)
    run_prv(epoch)
