from pathlib import Path

import click
from halo import Halo
from rich.console import Console

from sync_var import __version__
from sync_var.config import load_config
from sync_var.error import error_handle
from sync_var.logging import setup_logging
from sync_var.parse_master_var import parse_master_vars
from sync_var.parse_target_var import parse_target_files
from sync_var.replace import replace
from sync_var.save import save_target_files

console = Console(highlight=False)


@click.group(invoke_without_command=True)
@click.version_option(__version__, "--version", "-v", prog_name="sync-var")
@click.help_option("--help", "-h")
@click.pass_context
@error_handle
def root(ctx: click.Context) -> None:
    """A tool to synchronize variables across multiple files."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@root.command()
@click.help_option("--help", "-h")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
@error_handle
def init(config_path: str | None, verbose: bool) -> None:
    """Create template sync-var.yaml for configuration."""
    setup_logging(verbose)

    with Halo(text="Initializing configuration file...", spinner="dots") as spinner:
        _init_config_file(Path(config_path) if config_path else None)
        spinner.succeed("Configuration file initialized.")


@root.command()
@click.help_option("--help", "-h")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
@error_handle
def validate(config_path: str | None, verbose: bool) -> None:
    """Validate config file and master/target files."""
    setup_logging(verbose)

    with Halo(text="Loading configuration...", spinner="dots") as spinner:
        config = load_config(
            Path(config_path) if config_path else None,
            verbose=verbose,
        )
        spinner.succeed("Configuration loaded.")

    with Halo(text="Parsing master variable files...", spinner="dots") as spinner:
        master_vars = parse_master_vars(config.master_files)
        spinner.succeed("Master variable files parsed.")

    with Halo(text="Parsing target files...", spinner="dots") as spinner:
        parse_target_files(config.target_files, config.marker, master_vars)
        spinner.succeed("Target files parsed.")

    console.print("[green]Validation completed successfully.[/green]")


@root.command()
@click.help_option("--help", "-h")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file.",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    default=False,
    help="Dry run without making changes.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output results to the specified directory.",
)
@click.option(
    "--no-backup",
    "-n",
    is_flag=True,
    help="Overwrite target files without creating backup files.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
@error_handle
def sync(
    config_path: str | None,
    dry_run: bool,
    output_dir: str | None,
    no_backup: bool,
    verbose: bool,
) -> None:
    """Execute synchronization."""
    setup_logging(verbose)

    with Halo(text="Loading configuration...", spinner="dots") as spinner:
        config = load_config(
            Path(config_path) if config_path else None,
            dry_run=dry_run,
            output_dir=output_dir,
            no_backup=no_backup,
            verbose=verbose,
        )
        spinner.succeed("Configuration loaded.")

    with Halo(text="Parsing master variable files...", spinner="dots") as spinner:
        master_vars = parse_master_vars(config.master_files)
        spinner.succeed("Master variable files parsed.")

    with Halo(text="Parsing target files...", spinner="dots") as spinner:
        target_files = parse_target_files(
            config.target_files, config.marker, master_vars
        )
        spinner.succeed("Target files parsed.")

    with Halo(text="Replacing variables in target files...", spinner="dots") as spinner:
        replace(target_files, master_vars)
        spinner.succeed("Variables replaced in target files.")

    if config.save_options.dry_run:
        console.print("\n[bold yellow]Dry run mode:[/bold yellow]")
        save_target_files(target_files, config.save_options)
    else:
        with Halo(text="Saving target files...", spinner="dots") as spinner:
            save_target_files(target_files, config.save_options)
            spinner.succeed("Target files saved.")


def _init_config_file(config_path: Path | None) -> None:
    """Create a template sync-var.yaml configuration file."""
    output_path = config_path or Path("sync-var.yaml")

    if output_path.exists():
        raise FileExistsError(f"Configuration file already exists: {output_path}")

    template = """\
# sync-var configuration file
# See: https://github.com/suda-3156/sync-var

# Marker format: regex "\\[[0-9a-zA-Z_-]+\\]"
# marker: "[sync-var]"

# Master files containing variable definitions (.env or .yaml/.yml)
# "default" environment is required
master_files:
  default: path/to/default/master/file.env
  # staging: path/to/staging/master/file.env
  # prod: path/to/prod/master/file.yaml

# Shorthand for single default master file:
# master_files: path/to/default/master/file.env

# Target files to synchronize
target_files:
  - path/to/target/file.yaml
  # - path/to/another/target/file.sql
"""

    output_path.write_text(template, encoding="utf-8")
    console.print(f"Created configuration file: [cyan]{output_path}[/cyan]")
