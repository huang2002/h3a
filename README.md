# h3a

> A simple script for file archiving.

## Usage

```txt
Usage: h3a [OPTIONS]

  A simple script for file archiving.

Options:
  -c, --config FILE            Path to config file.  [default: h3a.yaml]
  -e, --encoding TEXT          Encoding of the config file.  [default: utf-8]
  -y, --skip-confirm           Skip confirmation prompt.
  -t, --threads INTEGER RANGE  Number of threads to use.  [x>=1]
  -d, --dry-run                Print plan and exit.
  --verbose                    Enable debug logging.
  --version                    Show the version and exit.
  --help                       Show this message and exit.
```

## Configuration

```yaml
include:  # required
  - foo.docx
  - bar/*.pptx
exclude:  # optional
  - bar/baz.pptx
tag_format: _v%Y%m%d-%H%M%S  # optional
tag_pattern: '_v\d{8}-\d{6}'  # optional
on_conflict: error  # optional
threads: 8  # optional
```

## License

ISC Licensed.
