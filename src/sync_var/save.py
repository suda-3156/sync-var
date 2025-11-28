from datetime import datetime
from pathlib import Path
from typing import List

from rich.console import Console

from sync_var.config import SaveOptions
from sync_var.parse_target_var import TargetFile

console = Console(highlight=False)


def save_target_files(
    target_files: List[TargetFile],
    options: SaveOptions,
) -> List[str]:
    if options.dry_run:
        _show_diff(target_files)
        return []

    if options.output_dir:
        logs = _save_to_output_dir(target_files, options.output_dir)
        return logs

    if options.no_backup:
        logs = _overwrite_target_files(target_files, create_backup=False)
        return logs

    logs = _overwrite_target_files(target_files, create_backup=True)
    return logs


def _show_diff(target_files: List[TargetFile]) -> None:
    has_changes = False

    for target_file in target_files:
        changes = [
            tl for tl in target_file.target_lines if tl.replaced_target_line is not None
        ]
        if not changes:
            continue

        has_changes = True
        console.print(f"\n[bold blue]{target_file.path}[/bold blue]")

        for target_line in changes:
            line_num = target_line.target_line_number
            before = target_line.raw_target_line
            after = (
                f"{target_line.target_line_indent}{target_line.replaced_target_line}"
            )
            if before == after:
                continue

            console.print(f"  Line {line_num}:")
            console.print(f"    [red]- {before}[/red]")
            console.print(f"    [green]+ {after}[/green]")

    if not has_changes:
        console.print("[yellow]No changes to apply.[/yellow]")


def _save_to_output_dir(
    target_files: List[TargetFile],
    output_dir: Path,
) -> List[str]:
    logs: List[str] = []

    output_dir.mkdir(parents=True, exist_ok=True)

    for target_file in target_files:
        content = _build_file_content(target_file)

        # generate output filename by replacing "/" with "_"
        output_filename = str(target_file.path).replace("/", "_")
        # remove leading "_" (for absolute paths)
        output_filename = output_filename.lstrip("_")

        output_path = output_dir / output_filename
        output_path.write_text(content, encoding="utf-8")

        logs.append(f"  Saved: [cyan]{output_path}[/cyan]")

    return logs


def _overwrite_target_files(
    target_files: List[TargetFile],
    create_backup: bool,
) -> List[str]:
    logs: List[str] = []

    for target_file in target_files:
        if not any(tl.replaced_target_line for tl in target_file.target_lines):
            continue

        if create_backup:
            backup_path = _create_backup(target_file.path)
            logs.append(f"  Backup: [dim]{backup_path}[/dim]")

        content = _build_file_content(target_file)
        target_file.path.write_text(content, encoding="utf-8")

        logs.append(f"  Updated: [cyan]{target_file.path}[/cyan]")

    return logs


def _create_backup(file_path: Path) -> Path:
    # backup format: filename.ext.bak.YYYYMMDDHHMMSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak.{timestamp}")

    # Copy the original file's content to the backup file
    backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

    return backup_path


def _build_file_content(target_file: TargetFile) -> str:
    with open(target_file.path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for target_line in target_file.target_lines:
        if target_line.replaced_target_line is None:
            continue

        line_index = target_line.target_line_number - 1  # 0-indexed
        indent = target_line.target_line_indent
        new_content = target_line.replaced_target_line

        # Preserve newline character if it existed
        original_line = lines[line_index]
        newline = "\n" if original_line.endswith("\n") else ""

        lines[line_index] = f"{indent}{new_content}{newline}"

    return "".join(lines)
