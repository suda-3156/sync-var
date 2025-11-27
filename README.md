# Sync Var

## TODO

- Currently, variable and environment names are case-sensitive. This should be changed to case-insensitive.

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
- `--config`, `-c`: path to config file
- `sync` command options
  - `default`: create backup in the format of `xxx.bak.YYYYMMDDHHMMSS`
  - `--dry-run`: dry run
  - `--output-dir`: output results to the specified directory; file names will be `"path/to/file".replace("/", "_")`
  - `--no-backup`: overwrite target files without creating backup files

### Config file format

File paths must be absolute or relative to the configuration file.

```yaml
marker: "[sync-var]" # default, regex "\[[0-9a-zA-Z_-]+\]", Case Insensitive

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

- Lines starting with the symbols below will be searched for markers.
  `#`, `//`, `///`, `////`, `--`, `;`, `'`, `::`, `REM`, `*`, `%`, `@`, `@@`, `!`, `<!--`

> Note: Although `<!--` supports multi-line comment blocks, this tool only processes the line immediately following the marker. Therefore, directives must be written on a single line.

### Directive examples

```yaml
server:
  # [sync-var] "api_key: {{ default.API_KEY }}"
  api_key: old_api_key
  # will be:
  api_key: new_api_key
```

```go
// [sync-var] "const BACKEND_URL = \"{{ prod.BACKEND_URL }}\""
const BACKEND_URL = "old.example.com"
// will be:
const BACKEND_URL = "new.example.com"
```

```sql
-- [sync-var] "GRANT CREATE ON {{ DB_NAME }}.* TO '{{ DB_USERNAME }}'@'%';"
GRANT CREATE ON old_db.* TO 'old_user'@'%';
-- will be:
GRANT CREATE ON new_db.* TO 'new_user'@'%';
```

## Future

- Structured target file configuration.
  - Wildcard support for path expressions
- Structured master values (in `.yaml`).
- Allow `.toml`, `.json` as master files
- Add `fallback default` mode/configuration.
  - If `env.VAR_NAME` is not found in the master files, its value will default to `default.VAR_NAME`
- Support comment block and warn if comment block has multiple lines.
- Support `--verbose` option for detailed logs.
