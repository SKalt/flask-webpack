# import json
from flask import Flask
from jinja2 import Markup, Context
from typing import (
    Callable,
    Union,
    Optional,
    List,
    Callable,
    Dict,
    # TypeVar,
)

_Whatev = Union[None, str, bytes, int]
# _MarkupValue = Union[str, bool, int]
_MarkupKvp = Dict[str, Union[str, bool, int]]

def _escape(s: str) -> str: ...


def _noop(*args: _Whatev, **kwargs: _Whatev) -> None: ...


def for_each_unique_chunk(
    chunk_urls: List[str],
    callback: Callable[[str], str]
) -> None: ...


def _markup_kvp(attrs: _MarkupKvp) -> str: ...


def _warn_missing(
    missing: str,
    type_info: str="asset",
    level: str="ERROR",
    log: Callable[[_Whatev], None]=_noop
) -> Markup: ...


class Webpack(object):
    def __init__(
        self,
        app: Optional[Flask]=None,
        assets_url: Optional[str]=None,
        manifest_path: Optional[str]=None,
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

    def javascript_tag(
        self,
        ctx: Context,
        *assets: str,
        unique: bool = True,
        attrs: _MarkupKvp = {},
        **more_attrs: Union[str, bool, int]
    ) -> Markup: ...

    def stylesheet_tag(
        self,
        ctx: Context,
        *assets: str,
        unique: bool = True,
        attrs: _MarkupKvp = {},
        **more_attrs: Union[str, bool, int]
    ) -> Markup: ...

    def asset_url_for(
        self,
        asset: str,
        warn_multiple: bool=True
    ) -> Optional[Markup]: ...

    def asset_urls_for(self, asset: str) -> Optional[List[str]]: ...

    def resolve_ext(
        self, asset: str, extensions: List[str]
    ) -> Optional[List[str]]: ...
