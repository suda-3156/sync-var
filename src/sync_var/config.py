import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set

import yaml

from sync_var.utils import file_exists

DEFAULT_MARKER = "[sync-var]"
DEFAULT_CONFIG_FILE = "sync-var.yaml"
CONFIG_FILE_SEARCH_PATHS = [
    "sync-var.yaml",
    "sync-var.yml",
    ".sync-var.yaml",
    ".sync-var.yml",
]


@dataclass
class SaveOptions:
    dry_run: bool = False
    output_dir: Optional[Path] = None
    no_backup: bool = False

    @property
    def backup(self) -> bool:
        return not self.no_backup


@dataclass
class Config:
    _master_files: Dict[str, str]
    _target_files: Set[str]
    marker: str = DEFAULT_MARKER
    config_file: str = DEFAULT_CONFIG_FILE
    save_options: SaveOptions = field(default_factory=SaveOptions)
    verbose: bool = False

    def __post_init__(self) -> None:
        self.validate_config()

    def validate_config(self) -> None:
        self._validate_marker()
        self._validate_master_files()
        self._validate_target_files()
        self._files_exist()

    def _validate_marker(self) -> None:
        if not self.marker:
            raise ValueError("Marker cannot be empty.")

        pattern = r"^\[[0-9a-zA-Z_-]+\]$"

        if not re.match(pattern, self.marker):
            raise ValueError(
                "Invalid marker format. Marker must be enclosed in square brackets "
                "and contain only alphanumeric characters, hyphens, or underscores."
            )
        return None

    def _validate_master_files(self) -> None:
        if not self._master_files:
            raise ValueError("At least one master file must be specified.")

        for name, path in self._master_files.items():
            if not name:
                raise ValueError("Master file names cannot be empty.")
            if not path:
                raise ValueError(f"Path for master file '{name}' cannot be empty.")

        if "default" not in self._master_files.keys():
            raise ValueError("A 'default' master file must be specified.")

    def _validate_target_files(self) -> None:
        if not self._target_files:
            raise ValueError("At least one target file must be specified.")

        for path in self._target_files:
            if not path:
                raise ValueError("Target file paths cannot be empty.")

        return None

    def _files_exist(self) -> None:
        errors = []
        for name, path in self.master_files.items():
            try:
                file_exists(path)
            except FileNotFoundError as e:
                errors.append(f"Master file '{name}': {e}")

        for path in self.target_files:
            try:
                file_exists(path)
            except FileNotFoundError as e:
                errors.append(f"Target file '{path}': {e}")

        if errors:
            raise ValueError("Configuration file errors:\n" + "\n".join(errors))

    @property
    def config_dir(self) -> Path:
        return Path(self.config_file).parent.resolve()

    @property
    def master_files(self) -> Dict[str, Path]:
        return {
            name: _resolve_path(path, self.config_dir)
            for name, path in self._master_files.items()
        }

    @property
    def target_files(self) -> Set[Path]:
        return {_resolve_path(path, self.config_dir) for path in self._target_files}


def _resolve_path(path: str | Path, base_dir: Path) -> Path:
    p = Path(path)
    # return absolute path as is
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def load_config(
    config_path: Optional[Path],
    dry_run: bool = False,
    output_dir: Optional[str] = None,
    no_backup: bool = False,
    verbose: bool = False,
) -> Config:
    file_path = _find_config_file(config_path)

    with open(file_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if config_data is None:
        raise ValueError("Configuration file is empty.")

    master_files = config_data.get("master_files", {})
    # Support shorthand: master_files: path/to/file.env → {"default": "path/to/file.env"}
    if isinstance(master_files, str):
        master_files = {"default": master_files}

    raw_target_files = config_data.get("target_files", [])
    target_files = (
        set(raw_target_files) if isinstance(raw_target_files, list) else set()
    )
    marker = config_data.get("marker", DEFAULT_MARKER)

    return Config(
        _master_files=master_files,
        _target_files=target_files,
        marker=marker,
        config_file=str(file_path),
        save_options=SaveOptions(
            dry_run=dry_run,
            output_dir=Path(output_dir) if output_dir else None,
            no_backup=no_backup,
        ),
        verbose=verbose,
    )


def _find_config_file(config_path: Optional[Path]) -> Path:
    file_path: Optional[Path] = None

    if config_path and config_path.exists():
        file_path = config_path
    else:
        for path_str in CONFIG_FILE_SEARCH_PATHS:
            path = Path(path_str)
            if path.exists():
                file_path = path
                break

    if file_path is None or not file_path.exists():
        raise FileNotFoundError("No configuration file found in default search paths.")

    if file_path.suffix not in {".yaml", ".yml"}:
        raise ValueError(
            "Configuration file must be a YAML file with .yaml or .yml extension."
        )

    return file_path
