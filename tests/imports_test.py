from collections.abc import Sequence
from types import ModuleType

from pytest import fixture


@fixture
def expected_module_names() -> Sequence[str]:
    import os

    import h3a

    module_dir: str = os.path.dirname(h3a.__file__)
    assert os.path.isdir(module_dir)

    return [
        os.path.splitext(module_name)[0]
        for module_name in os.listdir(module_dir)
        if module_name.endswith(".py") and not module_name.startswith("_")
    ]


def test_imports(expected_module_names: Sequence[str]) -> None:
    import h3a

    for module_name in expected_module_names:
        assert hasattr(h3a, module_name)
        assert isinstance(getattr(h3a, module_name), ModuleType)
