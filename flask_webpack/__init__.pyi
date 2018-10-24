# import json
from flask import Flask
from jinja2 import Markup
from typing import (
    Callable,
    Union,
    Optional,
    # TypeVar,
)

_Whatev = Union[None, str, bytes, int]


def _noop(*args: _Whatev, **kwargs: _Whatev) -> None: ...


def _markup_kvp(**attrs: Optional[Union[bool, str]]) -> str: ...


def _warn_missing(
    missing: str,
    type_info: str="asset",
    level: str="ERROR",
    log: Callable[[_Whatev], None]=_noop
) -> str: ...


class Webpack(object):
    def __init__(
        self,
        app: Optional[Flask]=None,
        assets_url: Optional[str]=None,
        **assets: str
    )-> None:
        ...

    def init_app(self, app: Flask) -> None: ...

    def _set_asset_paths(self, app: Flask) -> None: ...

    def _refresh_webpack_stats(self) -> None: ...

    def _warn_missing(
        self,
        missing: str,
        type_info: str="asset"
    ) -> None: ...

    def javascript_tag(self, *args: str) -> Markup: ...

    def stylesheet_tag(self, *args: str) -> Markup: ...

    def asset_url_for(self, asset: str) -> str: ...
