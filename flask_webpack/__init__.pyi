import json

from flask import current_app
from jinja2 import Markup
from logging import getLevelName
from typing import Any, Union, Optional


def _noop(*args: Any, **kwargs: Any) -> None: ...


def _warn_missing(
    missing: str,
    type_info: str="asset",
    level: str="ERROR",
    log: Callable[[Any], None]=_noop
) -> str: ...


class Webpack(object):
    def __init__(
        self: Any, app: Any=None, assets_url: Optional[str]=None,
        **assets: str
    )-> None:
        """Internalize the app context and add helpers to the app."""
        self.app = app
        self.assets_url = assets_url
        self.assets = assets
        if app is not None:
            self.init_app(app)
        else:
            self.log_level = "ERROR"
            self.log = _noop

    def init_app(self: Any, app: Any) -> None: ...

    def _set_asset_paths(self: Any, app: Any) -> None: ...

    def _refresh_webpack_stats(self: Any) -> None:

    def _warn_missing(
        self: Any, missing: str, type_info: str="asset"
    ) -> None: ...

    def javascript_tag(self: Any, *args: str) -> Markup: ...

    def stylesheet_tag(self: Any, *args: str) -> Markup:

    def asset_url_for(self, asset: str) -> str: ...
