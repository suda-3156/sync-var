# Concepts

## What is sync-var

A tool that automatically syncs configuration files that exist for each language or directory, and variables that you want to keep consistent across different files.

## Requirements

- Instructions for the next line (strictly the next line only) are given in a comment line.

### Commands

- `init`: Create a sample config file.
- `validate`: Read files based on the config file and validate the config file and target files.
- `sync`: Sync variables.
  - Default behavior: overwrite
  - `--backup` option: Create a backup.
  - `--output-dir` option: Specify the output directory.
  - `--dry-run` option: Do not actually make changes, only display the differences.

### Config File Format

- List file paths.
  - Allow specification by hierarchical structure in the future.
  - Wildcards will also be supported.
- masterfiles:
  - `default`: path/to/default/master/file (required)
  - In addition, list environment names and their master files (register environments here).

### Processing

Basically, perform replacement.

- Indentation is preserved separately (as tabs, spaces, and their counts may differ).
- Template format: `asdf {{ env.VAR_NAME }}`
  - If only the variable name is present, like `{{ VAR_NAME }}`, it refers to the `default` environment.

## Details

### Rules

- Only environments specified in the config + `default` are allowed.
  - `default` cannot be used as an environment name (reserved word).
- `environment.VAR_NAME` must be unique (syncing is performed using `environment.VAR_NAME` as the key).
- Environment name:
  - Alphanumeric characters, `-`, and `_` can be used (case-insensitive).
- Variable name:
  - Alphanumeric characters, `-`, and `_` can be used (case-insensitive).
- value:
  - Basically free (no restrictions as it is loaded by a Python package).
- Marker format:
  - Enclose in `[]`. Alphanumeric characters, `-`, and `_` can be used (case-insensitive).