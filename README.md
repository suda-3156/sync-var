# Sync Var

## Installation

```sh
pip install git+https://github.com/suda-3156/sync-var.git
```

## Usage

```sh
sync-var init # create template sync-var.yaml for configuration
sync-var validate # validate config file and master/target files
sync-var sync # execute synchronization
```

### Options

- `--help`, `-h` or just `sync-var`: display help
- `--version`, `-v`: display version
- `sync` command options
  - `default`: create backup in the format of `xxx.bak.YYYYMMDDHHMMSS`
  - `--dry-run`: dry run
  - `--output-dir`: output results to the specified directory; file names will be `"path/to/file".replace("/", "_")`
  - `--no-backup`: overwrite target files without creating backup files

### Config file format

```yaml
tag_format: "[sync-var]" # default, regex "\[[0-9a-zA-Z_-]+\]", Case Insensitive

master_files:
  - default: path/to/default/master/file.env # or .yaml, required
  # Allowed environment name: regex "[0-9a-zA-Z_-]+", must be unique, "default" is preserved.
  # Case Insensitive
  - custom_env_1: path/to/custom_env_1/master/file.yaml

# This is equivalent to setting only the default master file
# master_files: path/to/default/master/file.env

target_files:
  - path/to/target/file.env.dev
  - path/to/another/target/file.sql
```

### Variable name

Allowed pattern: regex `[0-9a-zA-Z_-]+`. `env.VAR_NAME` must be unique across environments.
Case Insensitive.

### Comment prefixes

- Lines starting with the symbols below will be searched for tags.
  `#`, `//`, `///`, `////`, `--`, `;`, `'`, `::`, `REM`, `*`, `%`, `@@`, `@`, `!`

## Future

- Structured target file configuration.
  - Wildcard support for path expressions
- Structured master values (in `.yaml`).
- Allow `.toml`, `.json` as master files
- Add `fallback default` mode/configuration.
  - If `env.VAR_NAME` is not found in the master files, its value will default to `default.VAR_NAME`
