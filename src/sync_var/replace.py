from typing import List
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
        corresponding_master_vars = [
            mv for mv in master_vars if is_corresponding_var(mv, target_line)
        ]
        if not corresponding_master_vars:
            continue

        replaced_line = target_line.replace_template
        for master_var in corresponding_master_vars:
            replaced_line = replaced_line.replace(
                f"{{{{ {master_var.env}.{master_var.key} }}}}",
                master_var.value,
            )

            if master_var.env == "default":
                replaced_line = replaced_line.replace(
                    f"{{{{ {master_var.key} }}}}",
                    master_var.value,
                )

        target_line.replaced_target_line = replaced_line


def is_corresponding_var(
    master_var: MasterVar,
    target_line: TargetLine,
) -> bool:
    master_var_name = master_var.key
    master_var_env = master_var.env

    target_line_vars = target_line.target_vars
    return (master_var_env, master_var_name) in target_line_vars
