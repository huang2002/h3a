from dataclasses import dataclass
from pathlib import Path
from subprocess import run

from pytest import fixture


@dataclass
class CodeBlock:
    language: str
    lines: list[str]


@fixture
def readme_code_blocks() -> list[CodeBlock]:
    code_blocks: list[CodeBlock] = []
    current_block: CodeBlock | None = None

    readme_path = Path(__file__).parent.parent / "README.md"
    with readme_path.open() as readme_file:
        for line in readme_file:
            if line.startswith("```"):
                if current_block is not None:
                    code_blocks.append(current_block)
                    current_block = None
                else:
                    current_block = CodeBlock(language=line[3:].strip(), lines=[])
            elif current_block is not None:
                current_block.lines.append(line)

    return code_blocks


def test_readme_help(readme_code_blocks: list[CodeBlock]) -> None:
    help_code_block: CodeBlock | None = None
    for help_code_block in readme_code_blocks:
        if (
            help_code_block.language == "sh"
            and help_code_block.lines[0].strip() == "$ h3a --help"
        ):
            break
    assert help_code_block, "Help code block not found!"
    process = run(["h3a", "--help"], check=True, capture_output=True, text=True)
    assert process.stdout == "".join(help_code_block.lines[1:])


def test_readme_help_config(readme_code_blocks: list[CodeBlock]) -> None:
    config_help_code_block: CodeBlock | None = None
    for config_help_code_block in readme_code_blocks:
        if (
            config_help_code_block.language == "sh"
            and config_help_code_block.lines[0].strip() == "$ h3a --help-config"
        ):
            break
    assert config_help_code_block, "Config help code block not found!"
    process = run(["h3a", "--help-config"], check=True, capture_output=True, text=True)
    assert process.stdout == "".join(config_help_code_block.lines[1:])


def test_readme_config(readme_code_blocks: list[CodeBlock]) -> None:
    config_code_block: CodeBlock | None = None
    for config_code_block in readme_code_blocks:
        if (
            config_code_block.language == "yaml"
            and config_code_block.lines[0].strip() == "# h3a.yaml"
        ):
            break
    assert config_code_block, "Config code block not found!"

    from h3a.config import load_config

    _config = load_config("".join(config_code_block.lines))
