# Architecture

## Logic

### Class

#### Target Variable Class

- file path
  - @property file name
- line num
  - マーカーコメントの行番号
  - @property target line num
- raw marker comment line
  - strip していない生の行を保持する
  - @property template
  - @property env
  - @property var_name
- raw target line
  - @property indent
  - @property content
- processed target line
  - 処理後の結果を保持する

```py
# インデントについて
def extract_indent(line: str) -> str:
    """行の先頭からインデント部分を抽出する"""
    match = re.match(r'^(\s*)', line)
    return match.group(1) if match else ''

# スペースインデント
line1 = "    value: 123"
indent1 = extract_indent(line1)  # "    " (4スペース)

# タブインデント
line2 = "\t\tvalue: 456"
indent2 = extract_indent(line2)  # "\t\t" (2タブ)

# 混合インデント
line3 = "\t  value: 789"
indent3 = extract_indent(line3)  # "\t  " (タブ+2スペース)
```

#### Master Variable Class

- source file path
- env
  - config ファイルで定義された環境のみ許可する
- var_name
- value

#### Config Class

- marker
- env list:
  - dict, holds master file path
- target file paths

### Process

#### Read master file/vars

YAML、ENV 形式に対応する YAML は一旦階層構造なしで、純粋に変数を読み取る

- 将来的に YAML の一階層に対応し、`xxx.yaml:default` や `xxx.yml:prod` で `default` 以下や `prod` 以下を参照できるようにする
- 将来的に TOML、JSON にも対応する

#### collect target vars

config で指定されたパスごとにファイルを読み取る

マスターに登録されていない `{{ 環境.変数名 }}` があればエラーとする

#### replace

テンプレートを実際の値で置換する

#### save (or show diffs in console)

以下の情報を用いて差分表示または保存を行う:

- raw target line
- processed target line
- line num

## Design

### validation

それぞれの処理について、validate → execute の順で実行する
`validate` コマンドは各処理の validate のみを実行する

### logging, verbose option

`rich.logging` を使用するデフォルトは warning 以上を表示
必要な情報は `console.print()` で出力するため、info は表示しない
`--verbose` オプション指定時は debug 以上を表示する

### error handling

エラーハンドリングには wrapper を使用する
