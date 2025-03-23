import os
from inspect import get_annotations
from typing import Final, Literal, TypedDict, cast

import strictyaml as yaml

DEFAULT_TAG_FORMAT = "_v%Y%m%d-%H%M%S"
DEFAULT_TAG_PATTERN = r"_v\d{8}-\d{6}"
DEFAULT_THREADS: Final = min(16, os.cpu_count() or 1)


# TODO: add config docs
class Config(TypedDict):
    include: list[str]
    exclude: list[str]
    tag_format: str
    tag_pattern: str
    on_conflict: Literal["error", "skip", "overwrite"]
    threads: int


config_schema = yaml.Map(
    {
        "include": yaml.Seq(yaml.Str()),
        yaml.Optional("exclude", default=[]): yaml.OrValidator(
            yaml.Seq(yaml.Str()),
            yaml.EmptyList(),
        ),
        yaml.Optional("tag_format", default=DEFAULT_TAG_FORMAT): yaml.Str(),
        yaml.Optional("tag_pattern", default=DEFAULT_TAG_PATTERN): yaml.Str(),
        yaml.Optional("on_conflict", default="error"): yaml.Enum(
            get_annotations(Config)["on_conflict"].__args__
        ),
        yaml.Optional("threads", default=DEFAULT_THREADS): yaml.Int(),
    }
)


def load_config(config_file_path: os.PathLike, encoding: str | None = None) -> Config:
    with open(config_file_path, "r", encoding=encoding) as config_file:
        return cast(
            Config,
            yaml.load(config_file.read(), config_schema).data,
        )
