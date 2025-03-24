import os
from inspect import get_annotations
from typing import Annotated, Final, Literal, NamedTuple, TypedDict, cast

import strictyaml as yaml

DEFAULT_TAG_FORMAT: Final = "_v%Y%m%d-%H%M%S"
DEFAULT_TAG_PATTERN: Final = r"_v\d{8}-\d{6}"
DEFAULT_ON_CONFLICT: Final = "error"
DEFAULT_THREADS: Final = min(16, os.cpu_count() or 1)


class ConfigItemMetaData(NamedTuple):
    required: bool
    help: str


# TODO: add config docs
class Config(TypedDict):
    include: Annotated[
        list[str],
        ConfigItemMetaData(
            required=True,
            help="An array of glob patterns to include.",
        ),
    ]
    exclude: Annotated[
        list[str],
        ConfigItemMetaData(
            required=False,
            help="An array of glob patterns to exclude. (default: [])",
        ),
    ]
    tag_format: Annotated[
        str,
        ConfigItemMetaData(
            required=False,
            help=f"The strftime format of the dest tag. (default: {DEFAULT_TAG_FORMAT!r})",
        ),
    ]
    tag_pattern: Annotated[
        str,
        ConfigItemMetaData(
            required=False,
            help=f"A regex pattern to match existing dest tags. (default: {DEFAULT_TAG_PATTERN!r})",
        ),
    ]
    on_conflict: Annotated[
        Literal["error", "skip", "overwrite"],
        ConfigItemMetaData(
            required=False,
            help=f"The action of existing dest files. (default: {DEFAULT_ON_CONFLICT!r})",
        ),
    ]
    threads: Annotated[
        int,
        ConfigItemMetaData(
            required=False,
            help=f"The number of maximum threads to use. (default: {DEFAULT_THREADS:d})",
        ),
    ]


config_schema = yaml.Map(
    {
        "include": yaml.Seq(yaml.Str()),
        yaml.Optional("exclude", default=[]): yaml.OrValidator(
            yaml.Seq(yaml.Str()),
            yaml.EmptyList(),
        ),
        yaml.Optional("tag_format", default=DEFAULT_TAG_FORMAT): yaml.Str(),
        yaml.Optional("tag_pattern", default=DEFAULT_TAG_PATTERN): yaml.Str(),
        yaml.Optional("on_conflict", default=DEFAULT_ON_CONFLICT): yaml.Enum(
            get_annotations(Config)["on_conflict"].__origin__.__args__
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


def format_config_help() -> str:
    help_text: str = ""
    for key, annotation in get_annotations(Config).items():
        assert hasattr(annotation, "__origin__")
        assert hasattr(annotation, "__metadata__")
        assert isinstance(annotation.__metadata__, tuple)
        assert len(annotation.__metadata__) == 1
        config_item_meta_data = annotation.__metadata__[0]
        assert isinstance(config_item_meta_data, ConfigItemMetaData)
        type_text: str = ""
        if annotation.__origin__ in {str, int, float, bool}:
            type_text += annotation.__origin__.__name__
        else:
            type_text += str(annotation.__origin__)
        if not config_item_meta_data.required:
            type_text += ", optional"
        help_text += f"{key} ({type_text}):\n    {config_item_meta_data.help}\n"
    return help_text
