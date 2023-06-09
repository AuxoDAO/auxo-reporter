

from dataclasses import dataclass
import json
from pathlib import Path

from reporter.models.Config import Config


@dataclass()
class RecipientWriter:
    config: Config
    directory: str = "reports"

    @property
    def path(self) -> str:
        return f"{self.directory}/{self.config.date}/compounding"

    def _create_dir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def increment_filename(self, name):
        """
        Check if the filename exists and if so, append a number to it
        """
        self._create_dir()
        i = 0
        while True:
            filename = f"{name}-{i}.json"
            filename_with_path = f"{self.path}/{filename}"

            if Path(filename_with_path).exists():
                i += 1
            else:
                return filename

    # write to a json file
    def to_json(self, data, name: str = "recipients") -> str:
        postfix_filename = self.increment_filename(name)
        with open(f"{self.path}/{postfix_filename}", "w+") as f:
            json.dump(data, f, indent=4)
        return postfix_filename
