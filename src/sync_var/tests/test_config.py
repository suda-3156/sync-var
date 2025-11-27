from pathlib import Path
from textwrap import dedent

import pytest

from sync_var.config import DEFAULT_MARKER, SaveOptions, load_config


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary config file."""
    return tmp_path / "sync-var.yaml"


@pytest.fixture
def create_files(tmp_path: Path):
    """Helper to create temporary files for testing."""

    def _create_files(*filenames: str) -> list[Path]:
        paths = []
        for filename in filenames:
            file_path = tmp_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            paths.append(file_path)
        return paths

    return _create_files


class TestLoadConfigSuccess:
    """Tests for successful config loading."""

    def test_load_config_full(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading a complete config file with all options."""
        create_files(
            "path/to/default.env",
            "path/to/staging.env",
            "path/to/target1.env",
            "path/to/target2.sql",
        )

        config_file.write_text(
            dedent(
                f"""\
            marker: "[custom-marker]"
            master_files:
              default: {tmp_path}/path/to/default.env
              staging: {tmp_path}/path/to/staging.env
            target_files:
              - {tmp_path}/path/to/target1.env
              - {tmp_path}/path/to/target2.sql
        """
            )
        )

        config = load_config(config_file)

        assert config.marker == "[custom-marker]"
        assert config.master_files == {
            "default": Path(f"{tmp_path}/path/to/default.env"),
            "staging": Path(f"{tmp_path}/path/to/staging.env"),
        }
        assert config.target_files == {
            Path(f"{tmp_path}/path/to/target1.env"),
            Path(f"{tmp_path}/path/to/target2.sql"),
        }
        assert config.config_file == str(config_file)
        # Default save options
        assert config.save_options.dry_run is False
        assert config.save_options.output_dir is None
        assert config.save_options.no_backup is False
        assert config.save_options.backup is True

    def test_load_config_minimal(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading a minimal config file (master_files and target_files only)."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.marker == DEFAULT_MARKER
        assert config.master_files == {"default": Path(f"{tmp_path}/master.env")}
        assert config.target_files == {Path(f"{tmp_path}/target.env")}

    def test_master_files_shorthand(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading config with shorthand master_files."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": Path(f"{tmp_path}/master.env")}
        assert config.target_files == {Path(f"{tmp_path}/target.env")}

    def test_load_config_yml_extension(self, tmp_path: Path, create_files) -> None:
        """Test loading config with .yml extension."""
        create_files("master.env", "target.env")

        config_file = tmp_path / "config.yml"
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": Path(f"{tmp_path}/master.env")}
        assert config.target_files == {Path(f"{tmp_path}/target.env")}

    def test_load_config_duplicated_master(self, tmp_path: Path, create_files) -> None:
        """Test loading config with duplicated master file keys (last one wins)."""
        create_files("another_master.env", "target.env")

        config_file = tmp_path / "config.yml"
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
              default: {tmp_path}/another_master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {
            "default": Path(f"{tmp_path}/another_master.env")
        }

    def test_load_config_duplicated_target_files(
        self, tmp_path: Path, create_files
    ) -> None:
        """Test loading config with duplicated target files (deduplicated to set)."""
        create_files("master.env", "target.env")

        config_file = tmp_path / "config.yml"
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.target_files == {Path(f"{tmp_path}/target.env")}


class TestLoadConfigFileErrors:
    """Tests for config file loading errors."""

    def test_load_config_empty_file(self, config_file: Path) -> None:
        """Test loading an empty config file."""
        config_file.write_text("")

        with pytest.raises(ValueError, match="empty"):
            load_config(config_file)

    def test_load_config_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a nonexistent config file."""
        nonexistent = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_invalid_extension(self, tmp_path: Path) -> None:
        """Test loading config with invalid file extension."""
        invalid_file = tmp_path / "config.json"
        invalid_file.write_text("{}")

        with pytest.raises(ValueError, match="YAML file"):
            load_config(invalid_file)


class TestLoadConfigValidationErrors:
    """Tests for config validation errors."""

    def test_load_config_empty_master_files(self, config_file: Path) -> None:
        """Test loading config with empty master_files raises error."""
        config_file.write_text(
            dedent(
                """\
            master_files:
            target_files:
              - target.env
        """
            )
        )

        with pytest.raises(ValueError, match="At least one master file"):
            load_config(config_file)

    def test_load_config_empty_target_files(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading config with empty target_files raises error."""
        create_files("master.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
        """
            )
        )

        with pytest.raises(ValueError, match="At least one target file"):
            load_config(config_file)

    def test_load_config_missing_default_master(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading config without 'default' master file raises error."""
        create_files("staging.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              staging: {tmp_path}/staging.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        with pytest.raises(ValueError, match="'default' master file"):
            load_config(config_file)

    def test_load_config_master_file_not_found(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading config with non-existent master file raises error."""
        create_files("target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/nonexistent.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        with pytest.raises(ValueError, match="File not found"):
            load_config(config_file)

    def test_load_config_target_file_not_found(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test loading config with non-existent target file raises error."""
        create_files("master.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/nonexistent.env
        """
            )
        )

        with pytest.raises(ValueError, match="File not found"):
            load_config(config_file)

    def test_load_config_multiple_files_not_found(
        self, config_file: Path, tmp_path: Path
    ) -> None:
        """Test loading config with multiple non-existent files shows all errors."""
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/missing_master.env
            target_files:
              - {tmp_path}/missing_target.env
        """
            )
        )

        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)

        error_message = str(exc_info.value)
        assert "missing_master.env" in error_message
        assert "missing_target.env" in error_message


class TestMarkerValidation:
    """Tests for marker format validation."""

    def test_valid_marker(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test valid marker formats."""
        create_files("master.env", "target.env")

        for marker in ["[sync-var]", "[CUSTOM]", "[my_marker]", "[test-123]"]:
            config_file.write_text(
                dedent(
                    f"""\
                marker: "{marker}"
                master_files:
                  default: {tmp_path}/master.env
                target_files:
                  - {tmp_path}/target.env
            """
                )
            )

            config = load_config(config_file)
            assert config.marker == marker

    def test_empty_marker(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test empty marker raises error."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            marker: ""
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        with pytest.raises(ValueError, match="empty"):
            load_config(config_file)

    def test_invalid_marker_format(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test invalid marker format raises error."""
        create_files("master.env", "target.env")

        invalid_markers = [
            "sync-var",  # missing brackets
            "[sync var]",  # contains space
            "[sync.var]",  # contains period
            "[]",  # empty content
            "[sync-var",  # missing closing bracket
            "sync-var]",  # missing opening bracket
        ]

        for marker in invalid_markers:
            config_file.write_text(
                dedent(
                    f"""\
                marker: "{marker}"
                master_files:
                  default: {tmp_path}/master.env
                target_files:
                  - {tmp_path}/target.env
            """
                )
            )

            with pytest.raises(ValueError, match="Invalid marker format"):
                load_config(config_file)


class TestSaveOptions:
    """Tests for SaveOptions configuration."""

    def test_save_options_defaults(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test default SaveOptions values."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.save_options.dry_run is False
        assert config.save_options.output_dir is None
        assert config.save_options.no_backup is False
        assert config.save_options.backup is True

    def test_save_options_dry_run(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test SaveOptions with dry_run enabled."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file, dry_run=True)

        assert config.save_options.dry_run is True
        assert config.save_options.no_backup is False

    def test_save_options_output_dir(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test SaveOptions with output_dir specified."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        output_dir = str(tmp_path / "output")
        config = load_config(config_file, output_dir=output_dir)

        assert config.save_options.output_dir == Path(output_dir)
        assert config.save_options.dry_run is False

    def test_save_options_no_backup(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test SaveOptions with no_backup enabled."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        config = load_config(config_file, no_backup=True)

        assert config.save_options.no_backup is True
        assert config.save_options.backup is False

    def test_save_options_backup_property(self) -> None:
        """Test SaveOptions.backup property is inverse of no_backup."""
        options_with_backup = SaveOptions(no_backup=False)
        assert options_with_backup.backup is True

        options_without_backup = SaveOptions(no_backup=True)
        assert options_without_backup.backup is False

    def test_save_options_all_options(
        self, config_file: Path, tmp_path: Path, create_files
    ) -> None:
        """Test SaveOptions with all options specified."""
        create_files("master.env", "target.env")

        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {tmp_path}/master.env
            target_files:
              - {tmp_path}/target.env
        """
            )
        )

        output_dir = str(tmp_path / "output")
        config = load_config(
            config_file,
            dry_run=True,
            output_dir=output_dir,
            no_backup=True,
        )

        assert config.save_options.dry_run is True
        assert config.save_options.output_dir == Path(output_dir)
        assert config.save_options.no_backup is True
        assert config.save_options.backup is False


class TestPathResolution:
    """Tests for relative path resolution based on config file location."""

    def test_relative_paths_resolved_from_config_dir(self, tmp_path: Path) -> None:
        """Relative paths should be resolved from config file's directory."""
        # Structure:
        # tmp_path/
        #   config/
        #     sync-var.yaml
        #   data/
        #     master.env
        #     target.env

        config_dir = tmp_path / "config"
        data_dir = tmp_path / "data"
        config_dir.mkdir()
        data_dir.mkdir()

        master_file = data_dir / "master.env"
        target_file = data_dir / "target.env"
        master_file.touch()
        target_file.touch()

        config_file = config_dir / "sync-var.yaml"
        config_file.write_text(
            dedent(
                """\
            master_files:
              default: ../data/master.env
            target_files:
              - ../data/target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": master_file.resolve()}
        assert config.target_files == {target_file.resolve()}

    def test_absolute_paths_unchanged(self, tmp_path: Path) -> None:
        """Absolute paths should remain unchanged."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        master_file = tmp_path / "master.env"
        target_file = tmp_path / "target.env"
        master_file.touch()
        target_file.touch()

        config_file = config_dir / "sync-var.yaml"
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: {master_file}
            target_files:
              - {target_file}
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": master_file}
        assert config.target_files == {target_file}

    def test_mixed_absolute_and_relative_paths(self, tmp_path: Path) -> None:
        """Config can have both absolute and relative paths."""
        config_dir = tmp_path / "config"
        data_dir = tmp_path / "data"
        config_dir.mkdir()
        data_dir.mkdir()

        master_file = data_dir / "master.env"
        target_file = data_dir / "target.env"
        master_file.touch()
        target_file.touch()

        config_file = config_dir / "sync-var.yaml"
        config_file.write_text(
            dedent(
                f"""\
            master_files:
              default: ../data/master.env
            target_files:
              - {target_file}
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": master_file.resolve()}
        assert config.target_files == {target_file}

    def test_config_dir_property(self, tmp_path: Path) -> None:
        """config_dir property returns the directory of the config file."""
        config_dir = tmp_path / "nested" / "config"
        config_dir.mkdir(parents=True)

        master_file = config_dir / "master.env"
        target_file = config_dir / "target.env"
        master_file.touch()
        target_file.touch()

        config_file = config_dir / "sync-var.yaml"
        config_file.write_text(
            dedent(
                """\
            master_files:
              default: master.env
            target_files:
              - target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.config_dir == config_dir.resolve()

    def test_same_directory_relative_paths(self, tmp_path: Path) -> None:
        """Relative paths in same directory as config file work correctly."""
        master_file = tmp_path / "master.env"
        target_file = tmp_path / "target.env"
        master_file.touch()
        target_file.touch()

        config_file = tmp_path / "sync-var.yaml"
        config_file.write_text(
            dedent(
                """\
            master_files:
              default: master.env
            target_files:
              - target.env
        """
            )
        )

        config = load_config(config_file)

        assert config.master_files == {"default": master_file.resolve()}
        assert config.target_files == {target_file.resolve()}
