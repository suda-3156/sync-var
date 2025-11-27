# Architecture

## Logic

### Class

#### Target Line Class

- file path
- marker line num
  - Line number of the marker comment
  - @property target line num
- raw marker comment line
  - Holds the raw line without stripping
  - @property template
  - @property env
  - @property var_name
- raw target line
  - @property indent
  - @property content
- replaced target line
  - Holds the result after processing

```py
# Regarding indentation
def extract_indent(line: str) -&gt; str:
    &quot;&quot;&quot;Extracts the indent part from the beginning of a line&quot;&quot;&quot;
    match = re.match(r&#x27;^(\s*)&#x27;, line)
    return match.group(1) if match else &#x27;&#x27;

# Space indent
line1 = &quot;    value: 123&quot;
indent1 = extract_indent(line1)  # &quot;    &quot; (4 spaces)

# Tab indent
line2 = &quot;\t\tvalue: 456&quot;
indent2 = extract_indent(line2)  # &quot;\t\t&quot; (2 tabs)

# Mixed indent
line3 = &quot;\t  value: 789&quot;
indent3 = extract_indent(line3)  # &quot;\t  &quot; (tab + 2 spaces)
```

#### Master Variable Class

- source file path
- env
  - Only allow environments defined in the config file -&gt; Since the environment and master file are defined at the same time, no problems will occur
- var_name
- value

#### Config Class

- marker
- env list:
  - dict, holds master file path
- target file paths

### Process

#### Read master file/vars

Supports YAML and ENV formats. For now, YAML is read without hierarchical structure, purely reading variables.

- In the future, support one level of hierarchy in YAML, allowing references to sections under `default` or `prod` with `xxx.yaml:default` or `xxx.yml:prod`.
- In the future, also support TOML and JSON.

#### collect target vars

Read files for each path specified in the config.

If a `{{ environment.variable_name }}` not registered in the master is found, it will be an error.

#### replace

Replace the template with the actual value.

#### save (or show diffs in console)

Perform diff display or save using the following information:

- raw target line
- processed target line
- line num

## Design

### error handling

Use a wrapper for error handling.

- TODO:

### validation

For each process, execute in the order of validate → execute.
The `validate` command executes only the validation of each process.

### logging, verbose option

Use `rich.logging`. By default, display warnings and above.
Necessary information is output with `console.print()`, so info is not displayed.
When the `--verbose` option is specified, display debug and above.
