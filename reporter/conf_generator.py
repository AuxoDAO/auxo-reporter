from pathlib import Path
from pydantic import parse_file_as
import json
import calendar
import datetime

from reporter.types import Config, Reward, InputConfig


def get_dates(month: int, year: int):
    (_, n_days) = calendar.monthrange(year, month)

    date = datetime.date(year, month, 1)
    start_date = datetime.datetime(year, month, 1, 0, 0, 0)
    end_date = datetime.datetime(year, month, n_days, 23, 59, 59)

    return (date, start_date, end_date)


def create_conf(path: str) -> Config:
    """Generates the base config object from user input"""
    base_config = parse_file_as(InputConfig, path)

    (date, start_date, end_date) = get_dates(base_config.month, base_config.year)

    return Config(
        date=f"{date.year}-{date.month}",
        start_timestamp=int(start_date.timestamp()),
        end_timestamp=int(end_date.timestamp()),
        **base_config.dict(),
    )


def load_conf(config_path: str) -> Config:
    """Loads an existing config from file"""
    return parse_file_as(Config, path=f"{config_path}/epoch-conf.json")


def main() -> str:
    """Generates config file and saves in newly created directory with correct strcutre"""
    path_to_config_file = input(" Path to the config file ")
    conf = create_conf(path_to_config_file)

    # create directories
    epoch = f"reports/{conf.date}"
    Path(epoch).mkdir(parents=True, exist_ok=True)
    Path(f"{epoch}/csv/").mkdir(parents=True, exist_ok=True)
    Path(f"{epoch}/json/").mkdir(parents=True, exist_ok=True)

    # write new config file
    with open(f"{epoch}/epoch-conf.json", "w+") as j:
        j.write(json.dumps(conf.dict(), indent=4))

    print(f"😃 Created a new epoch folder reports/{conf.date}")

    return epoch
