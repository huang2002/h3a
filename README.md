# h3a

> A simple script for file archiving.

- Python: >=3.12
- Test Coverage: 100%
- Well Typed: Yes
- License: ISC

## Usage

```sh
$ h3a --help
Usage: h3a [OPTIONS]

  A simple script for file archiving.

Options:
  -c, --config FILE            Path to config file.  [default: h3a.yaml]
  -e, --encoding TEXT          Encoding of the config file.  [default: utf-8]
  --help-config                Show config schema and exit.
  -y, --skip-confirm           Skip confirmation prompt.
  -t, --threads INTEGER RANGE  Number of threads to use.  [x>=1]
  --dry-run                    Print plan and exit.
  --verbose                    Enable info-level logging.
  --debug                      Enable debug-level logging.
  --version                    Show the version and exit.
  --help                       Show this message and exit.
```

## Example

Say you wanna archive all the Office files in the current directory except the ones starts with `_`:

```txt
some_directory/
+-- foo.docx
+-- bar.pptx
+-- baz.xlsx
`-- _blah.docx
```

You can first create a config file `h3a.yaml`:

```yaml
# h3a.yaml
include:
  - '**/*.docx'
  - '**/*.pptx'
  - '**/*.xlsx'
exclude:
  - '_*.*'
on_conflict: overwrite
```

Then, execute `h3a` in the directory and confirm the archive plan:

```sh
h3a
```

Now you get your files archived: (The actual time tag differs.)

```txt
some_directory/
+-- h3a.yaml
+-- foo.docx
+-- foo_v20251024-123456.docx
+-- bar.pptx
+-- bar_v20251024-123456.pptx
+-- baz.xlsx
+-- baz_v20251024-123456.xlsx
`-- _blah.docx
```

## Configuration Schema

```sh
$ h3a --help-config
include (list[str]):
    An array of glob patterns to include.
exclude (list[str], optional):
    An array of glob patterns to exclude. (default: [])
out_dir (str, optional):
    The output path prefix.
tag_format (str, optional):
    The strftime format of the dest tag. (default: '_v%Y%m%d-%H%M%S')
tag_pattern (str, optional):
    A regex pattern to match existing dest tags. (default: '_v\\d{8}-\\d{6}')
on_conflict (typing.Literal['error', 'skip', 'overwrite'], optional):
    The action of existing dest files. (default: 'error')
threads (int, optional):
    The number of maximum threads to use. (default: 8)
```
