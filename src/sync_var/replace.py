import re
from typing import Dict, List, Tuple

from sync_var.logging import log
from sync_var.parse_master_var import MasterVar
from sync_var.parse_target_var import TargetFile, TargetLine


def replace(
    target_files: List[TargetFile],
    master_vars: List[MasterVar],
) -> None:

    for target_file in target_files:
        replace_target_lines(target_file, master_vars)


def replace_target_lines(
    target_file: TargetFile,
    master_vars: List[MasterVar],
) -> None:
    for target_line in target_file.target_lines:
        log.debug(
            f"Replacing variables in {target_file.path} at line {target_line.marker_line_number}"
        )
        corresponding_vars: List[Tuple[MasterVar, Tuple[str, str]]] = []
        for master_var in master_vars:
            corresponding_vars.extend(get_corresponding_vars(master_var, target_line))

        if not corresponding_vars:
            log.debug(
                f"No corresponding master vars found for {target_file.path} at line {target_line.marker_line_number}"
            )
            continue

        log.debug(
            f"Found corresponding master vars for {target_file.path} at line {target_line.marker_line_number}: "
            f"{[(mv.env, mv.key) for mv, _ in corresponding_vars]}"
        )

        replaced_line = target_line.replace_template
        log.debug(f"Replace template: {replaced_line}")

        for master_var, target_var in corresponding_vars:
            replaced_line = replaced_line.replace(
                f"{{{{ {target_var[0]}.{target_var[1]} }}}}",
                master_var.value,
            )
            log.debug(
                f"Replaced {{{{ {target_var[0]}.{target_var[1]} }}}} with {master_var.value}"
            )

            if master_var.env == "default":
                replaced_line = replaced_line.replace(
                    f"{{{{ {target_var[1]} }}}}",
                    master_var.value,
                )
                log.debug(f"Replaced {{{{ {target_var[1]} }}}} with {master_var.value}")

        log.debug(f"Final replaced line: {replaced_line}")
        target_line.replaced_target_line = replaced_line


def get_corresponding_vars(
    master_var: MasterVar,
    target_line: TargetLine,
) -> List[Tuple[MasterVar, Tuple[str, str]]]:
    # Return list of (MasterVar, (env, key)) tuples that correspond to the given master_var
    corresponding_vars = []
    for env, key in target_line.target_vars:
        if master_var.env == env.lower() and master_var.key == key.upper():
            corresponding_vars.append((master_var, (env, key)))
    return corresponding_vars
