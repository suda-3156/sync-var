from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, List, Set, Tuple

from sync_var.parse_master_var import MasterVar


COMMENT_PREFIX = [
    "#",
    "//",
    "///",
    "////",
    "--",
    ";",
    "'",
    "%",
    "::",
    "REM",
    "*",
    "%",
    "@",
    "@@",
    "!",
    "<!--",
]


@dataclass
class TargetLine:
    _marker: str
    source_file: Path
    marker_line_number: int
    raw_marker_line: str
    raw_target_line: str
    replaced_target_line: Optional[str]

    @property
    def target_line_number(self) -> int:
        return self.marker_line_number + 1

    @property
    def replace_template(self) -> str:
        content = strip_comment_simbols(self.raw_marker_line)
        marker_removed = strip_marker(content, self._marker)

        # Expecting the value to be enclosed in double quotes
        pattern = re.compile(r'^"((?:[^"\\]|\\.)*)"')
        match = pattern.match(marker_removed)
        if not match:
            raise ValueError(
                f"Invalid marker line format at line {self.marker_line_number}: "
                "Expected a value enclosed in double quotes."
            )
        return match.group(1)

    @property
    def target_vars(self) -> List[Tuple[str, str]]:
        # returns list of (env, key)

        # Match all unescaped {{ key }} patterns.
        pattern = re.compile(r"(?<!\\)\{\{\s*([^{}]+?)\s*\}\}")
        match = pattern.findall(self.replace_template)
        if not match:
            raise ValueError(
                f"No valid variable placeholders found in marker line at line "
                f"{self.marker_line_number}."
            )

        result = []
        for var in match:
            if "." not in var:
                result.append(("default", var.strip()))
            else:
                env, key = var.split(".", 1)
                result.append((env.strip(), key.strip()))

        return result

    @property
    def target_line_indent(self) -> str:
        match = re.match(r"^(\s*)", self.raw_target_line)
        return match.group(1) if match else ""

    @property
    def target_line_content(self) -> str:
        return self.raw_target_line.strip()


@dataclass
class TargetFile:
    path: Path
    target_lines: List[TargetLine]


def parse_target_files(
    target_files: Set[Path], marker: str, master_vars: List[MasterVar]
) -> List[TargetFile]:
    target_file_objs: List[TargetFile] = []

    errors = []
    for path in target_files:
        try:
            target_lines = _parse_target_file(path, marker)
            validate_target_lines(target_lines, master_vars)
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue

        target_file_obj = TargetFile(
            path=path,
            target_lines=target_lines,
        )
        target_file_objs.append(target_file_obj)

    if errors:
        raise ValueError("Errors while parsing target files:\n" + "\n".join(errors))

    return target_file_objs


def _parse_target_file(path: Path, marker: str) -> List[TargetLine]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    target_lines: List[TargetLine] = []
    for i, line in enumerate(lines):
        if not is_marker_line(line, marker):
            continue

        raw_marker_line = line.rstrip("\n")
        raw_target_line = lines[i + 1].rstrip("\n") if i + 1 < len(lines) else ""

        target_line = TargetLine(
            _marker=marker,
            source_file=path,
            marker_line_number=i + 1,
            raw_marker_line=raw_marker_line,
            raw_target_line=raw_target_line,
            replaced_target_line=None,
        )

        target_lines.append(target_line)

    return target_lines


def validate_target_lines(
    target_lines: List[TargetLine], master_vars: List[MasterVar]
) -> None:
    # Check if (env, key) pairs exists in master vars
    for target_line in target_lines:
        for env, key in target_line.target_vars:
            if not any(mv.env == env and mv.key == key for mv in master_vars):
                raise ValueError(
                    f"Variable '{key}' with environment '{env}' in target file "
                    f"at line {target_line.marker_line_number} "
                    "not found in any master variable files."
                )


def is_comment_line(line: str) -> bool:
    stripped_line = line.strip()
    for prefix in COMMENT_PREFIX:
        if stripped_line.startswith(prefix):
            return True
    return False


def is_marker_line(line: str, marker: str) -> bool:
    stripped_line = line.strip()
    if is_comment_line(stripped_line):
        content = strip_comment_simbols(stripped_line)
        return content.startswith(marker)

    return False


def strip_comment_simbols(line: str) -> str:
    stripped_line = line.strip()
    for prefix in COMMENT_PREFIX:
        if stripped_line.startswith(prefix):
            return stripped_line[len(prefix) :].lstrip()
    return stripped_line


def strip_marker(line: str, marker: str) -> str:
    stripped_line = line.strip()
    if stripped_line.startswith(marker):
        return stripped_line[len(marker) :].lstrip()
    return stripped_line
