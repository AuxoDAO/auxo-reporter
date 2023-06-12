from dataclasses import dataclass
import json
from pathlib import Path

from reporter.models.Config import CompoundConf


@dataclass()
class RecipientWriter:
    config: CompoundConf

    @property
    def path(self) -> str:
        return f"{self.config.directory}/{self.config.date}/compounding"

    def _create_dir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    # write to a json file
    def to_json(self, data, name: str = "recipients") -> str:
        self._create_dir()
        filename = f"{name}-{self.config.compound_epoch}.json"
        with open(f"{self.path}/{filename}", "w") as f:
            json.dump(data, f, indent=4)
        return filename
