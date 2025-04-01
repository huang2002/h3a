from inspect import get_annotations
from typing import Annotated, Final, Literal, NamedTuple, TypeAliasType, TypedDict, cast

import strictyaml as yaml

type OnConflictType = Literal["error", "skip", "overwrite"]

DEFAULT_TAG_FORMAT: Final = "_v%Y%m%d-%H%M%S"
DEFAULT_TAG_PATTERN: Final = r"_v\d{8}-\d{6}"
DEFAULT_ON_CONFLICT: Final = "error"
DEFAULT_THREADS: Final = 8


class ConfigItemMetaData(NamedTuple):
    required: bool
    help: str


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
    out_dir: Annotated[
        str,
        ConfigItemMetaData(
            required=False,
            help="The output path prefix.",
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
        OnConflictType,
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


class ExtraConfig(TypedDict, total=False):
    _execute_delay_seconds: float


config_schema = yaml.Map(
    {
        "include": yaml.Seq(yaml.Str()),
        yaml.Optional("exclude", default=[]): yaml.OrValidator(
            yaml.Seq(yaml.Str()),
            yaml.EmptyList(),
        ),
        yaml.Optional("out_dir", default=""): yaml.Str(),
        yaml.Optional("tag_format", default=DEFAULT_TAG_FORMAT): yaml.Str(),
        yaml.Optional("tag_pattern", default=DEFAULT_TAG_PATTERN): yaml.Str(),
        yaml.Optional("on_conflict", default=DEFAULT_ON_CONFLICT): yaml.Enum(
            OnConflictType.__value__.__args__
        ),
        yaml.Optional("threads", default=DEFAULT_THREADS): yaml.Int(),
        yaml.Optional("_execute_delay_seconds", default=0.0): yaml.Float(),
    }
)

EXTRA_CONFIG_KEYS = frozenset[str](get_annotations(ExtraConfig).keys())


def load_config(yaml_string: str, *, extras: ExtraConfig | None = None) -> Config:
    config = cast(Config, yaml.load(yaml_string, config_schema).data)
    if extras is not None:
        for key in EXTRA_CONFIG_KEYS:
            extras[key] = config.pop(key)
    else:
        for key in EXTRA_CONFIG_KEYS:
            config.pop(key)
    return config


def format_config_help() -> str:
    help_text: str = ""

    for key, annotation in get_annotations(Config).items():
        assert hasattr(annotation, "__origin__")
        assert hasattr(annotation, "__metadata__")
        assert isinstance(annotation.__metadata__, tuple)
        assert len(annotation.__metadata__) == 1

        config_item_meta_data = annotation.__metadata__[0]
        assert isinstance(config_item_meta_data, ConfigItemMetaData)

        annotation_type = annotation.__origin__
        while isinstance(annotation_type, TypeAliasType):
            annotation_type = annotation_type.__value__

        type_text: str = ""
        if annotation_type in {str, int, float, bool}:
            type_text += annotation_type.__name__
        else:
            type_text += str(annotation_type)
        if not config_item_meta_data.required:
            type_text += ", optional"

        help_text += f"{key} ({type_text}):\n    {config_item_meta_data.help}\n"

    return help_text
