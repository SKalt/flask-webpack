from typing import (
    # TypeVar,
    Dict,
    Callable,
    Any,
)
from jinja2 import Markup


class Flask(object):
    context: Dict[str, str]

    def before_request(self, arg: Callable[..., Any]) -> None: ...

    def add_template_global(self, fn: Callable[..., Markup]) -> None: ...


current_app: Flask
