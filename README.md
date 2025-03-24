# h3a

> A simple script for file archiving.

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
  -d, --dry-run                Print plan and exit.
  --verbose                    Enable debug logging.
  --version                    Show the version and exit.
  --help                       Show this message and exit.
```

## Example Configuration

```yaml
# h3a.yaml
include:
  - '*.docx'
  - '*.pptx'
  - '*.xlsx'
exclude:
  - '_*.*'
on_conflict: overwrite
```

## Configuration Schema

```sh
$ h3a --help-config
include (list[str]):
    An array of glob patterns to include.
exclude (list[str], optional):
    An array of glob patterns to exclude. (default: [])
tag_format (str, optional):
    The strftime format of the dest tag. (default: '_v%Y%m%d-%H%M%S')
tag_pattern (str, optional):
    A regex pattern to match existing dest tags. (default: '_v\\d{8}-\\d{6}')
on_conflict (typing.Literal['error', 'skip', 'overwrite'], optional):
    The action of existing dest files. (default: 'error')
threads (int, optional):
    The number of maximum threads to use. (default: 16)
```

## License

ISC Licensed.
