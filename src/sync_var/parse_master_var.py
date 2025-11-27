from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List
from dotenv import dotenv_values
import yaml


@dataclass
class MasterVar:
    source_file: Path
    env: str
    key: str
    value: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.key:
            raise ValueError("Key cannot be empty.")

        pattern = r"^[0-9a-zA-Z_-]+$"

        if not re.match(pattern, self.key):
            raise ValueError(
                "Invalid key format. Key must contain only alphanumeric characters, hyphens, or underscores."
            )

        return None


def parse_master_vars(master_files: Dict[str, Path]) -> List[MasterVar]:
    master_vars: List[MasterVar] = []

    errors = []
    for env, path in master_files.items():
        try:
            vars_in_file = _parse_master_file(path, env)
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue
        master_vars.extend(vars_in_file)

    if errors:
        raise ValueError("Errors while parsing master files:\n" + "\n".join(errors))

    validate_master_vars(master_vars)

    return master_vars


def _parse_master_file(path: Path, env: str) -> List[MasterVar]:
    if path.suffix in {".yaml", ".yml"}:
        return _parse_master_yaml_file(path, env)

    if ".env" in path.name:
        return _parse_master_env_file(path, env)

    raise ValueError(f"Unsupported master file format: {path.suffix} for file {path}.")


def _parse_master_env_file(path: Path, env: str) -> List[MasterVar]:
    master_vars: List[MasterVar] = []

    errors = []
    env_vars = dotenv_values(dotenv_path=path)
    for key, value in env_vars.items():
        if value is not None:
            try:
                master_var = MasterVar(
                    source_file=path,
                    env=env,
                    key=key,
                    value=value,
                )
            except ValueError as e:
                errors.append(str(e))
                continue

            master_vars.append(master_var)

        else:
            errors.append(f"Value for key: {key} in {path} is None.")

    if errors:
        raise ValueError("Errors while parsing *.env* file:\n" + "\n".join(errors))

    return master_vars


def _parse_master_yaml_file(path: Path, env: str) -> List[MasterVar]:
    master_vars: List[MasterVar] = []

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    errors = []
    for key, value in data.items():
        try:
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    f"Key: {key} and value: {value} in {path} must be strings."
                )
            master_var = MasterVar(
                source_file=path,
                env=env,
                key=key,
                value=value,
            )
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue

        master_vars.append(master_var)

    if errors:
        raise ValueError("Errors while parsing YAML file:\n" + "\n".join(errors))

    return master_vars


def validate_master_vars(master_vars: List[MasterVar]) -> None:
    seen = set()
    for var in master_vars:
        identifier = (var.env, var.key)
        if identifier in seen:
            raise ValueError(
                f"Duplicate master variable found: file '{var.source_file}', "
                f"env '{var.env}', key '{var.key}'."
            )
        seen.add(identifier)
