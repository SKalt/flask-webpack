"""jinja2 helpers to include processed files using the names of source files.
"""
__version__ = "0.0.1"
import os
import json

from flask import current_app, Flask
from jinja2 import Markup, contextfunction
from werkzeug.routing import BuildError
from logging import getLevelName

from typing import Any, Callable, Dict, List, Union, cast

JsonPrimitive = Union[None, str, bytes, int, float]
JsonValue = Dict[str, JsonPrimitive]
MarkupKvp = Dict[str, Union[str, bool, int, float]]
ChunkDef = str


def _noop(*args: Any, **kwargs: Any) -> None:
    pass


def _merge(*key_value_pairs: Dict[str, JsonPrimitive]):
    return {key: value for kvp in key_value_pairs for key, value in kvp.items()}


def _get_attrs(attrs: Dict[str, JsonValue]) -> JsonValue:
    """hoist the keys and value of a nested "attrs" dict to the top level.
    This is useful for passing duplicate kwargs or avoiding reserved keywords
    by passing them as string keys.
    This hositing functionality could have been written as
        fn(attrs={}, **more_attrs): return {**attrs, **more_attrs}
    but is included for python 2.7 compatibility.

    Args:
        attrs (nested dict): HTML tag attributes

    Returns:
        dict: unnested HTML tag attributes.

    Examples:
    >>> _get_attrs(dict(attrs={'async': True})) # dict(async=1) throws in python 3.7
    {'async': true}
    """
    _attrs = attrs.pop("attrs", {})  # type: Union[JsonValue, JsonPrimitive]
    _mutated = cast(JsonValue, attrs)  # type: JsonValue
    if type(_attrs) is dict:
        return _merge(_mutated, cast(JsonValue, _attrs))
    elif type(_attrs) in (str, int, float, bool):
        return _merge(_mutated, {"attrs": cast(JsonPrimitive, _attrs)})
    # throw error here
    return _mutated


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _markup_kvp(**attrs: JsonValue) -> str:
    """helper: returns str HTML-style key-value pairs"""
    return " ".join(
        key if value is True else '{}="{}"'.format(key, _escape(str(value)))
        for key, value in _get_attrs(attrs).items()
        if value is not False
    )


def for_each_unique_chunk(
    ctx,
    chunks: List[ChunkDef],
    callback: Callable[[ChunkDef], Any],
    unique: bool = True,
) -> None:
    if not hasattr(ctx.eval_ctx, "webpack_included_assets"):
        ctx.eval_ctx.webpack_included_assets = set()
    used = ctx.eval_ctx.webpack_included_assets  # type: set
    for chunk in chunks:
        if chunk not in used or not unique:
            used.add(chunk)
            callback(chunk)


def _warn(
    asset_name: str = "",
    message: str = "",
    type_info: str = "asset",
    level: str = "ERROR",
    log: Callable[[str], None] = _noop,
    values: Dict = {},
) -> Markup:
    log(message)

    def js_warn(fn, msg):
        msg = msg.replace('"', '\\"')  # escape double qotes for JS safety
        return Markup(
            '<script>{fn}("{msg}")</script>'.format(fn=fn, msg=_escape(msg))
        )

    if level == "DEBUG":
        return Markup("<!-- {} -->".format(_escape(message.replace("-->", ""))))
    elif level == "INFO":
        return js_warn("console.warn", message)
    elif level == "WARNING":
        return js_warn("console.error", message)

    raise BuildError(asset_name, values, (type_info,))
    return Markup("")  # never reached; only for typing


def _warn_missing(
    asset_name: str,
    type_info: str = "asset",
    level: str = "ERROR",
    log: Callable = _noop,
    values: Dict = {},
) -> Markup:
    message = "[flask-webpack] missing {type_info} {missing}".format(
        type_info=type_info, missing=asset_name
    )
    return _warn(
        asset_name=asset_name,
        message=message,
        type_info=type_info,
        log=log,
        level=level,
        values=values,
    )


def _warn_multiple(
    asset_name: str,
    type_info: str = "asset",
    level: str = "ERROR",
    log: Callable = _noop,
    values: Dict = {},
) -> Markup:
    message = (
        "[flask-webpack] only one of multiple chunks of {type_info} "
        "{asset_name} requested"
    ).format(type_info=type_info, asset_name=asset_name)
    return _warn(
        asset_name=asset_name,
        message=message,
        type_info=type_info,
        log=log,
        level=level,
        values=values,
    )


class Webpack(object):
    def __init__(
        self,
        app: Flask = None,
        assets_url: str = "",
        log_level: str = "ERROR",
        manifest_path: str = None,
        **assets: ChunkDef
    ):
        """
        Internalize the app context and add helpers to the app.
        :param app: the flask app
        :param assets_url: a URL to prefex all assets with
        :param manifest_path: the path to a JSON name/filename asset map
        :param assets: a JSON name/filename asset map
        """
        self.app = app
        self.assets_url = assets_url or ""
        self.assets = assets
        self.manifest_path = manifest_path
        self.log_level = log_level or "ERROR"
        if app is not None:
            self.init_app(app)
        else:
            self.log_level = "ERROR"
            self.log = cast(Callable[[str], None], _noop)

    def init_app(self, app: Flask) -> None:
        """
        Mutate the application passed in as explained here:
        http://flask.pocoo.org/docs/latest/extensiondev/

        :param app: Flask application
        :return: None
        """
        debug = (
            app.config.get("DEBUG")
            or os.environ.get("FLASK_DEBUG")
            or os.environ.get("FLASK_ENV") == "development"
        )
        log_level = (
            app.config.get("WEBPACK_LOG_LEVEL")
            or ("DEBUG" if debug else None)
            or self.log_level
            or "ERROR"
        )

        def log(message: str) -> None:
            app.logger.log(getLevelName(log_level), message)

        if log_level:
            self.log_level = log_level
            self.log = log

        # Setup a few sane defaults
        app.config.setdefault("WEBPACK_ASSETS_URL", None)
        self._set_asset_paths(app)

        # We only want to refresh the webpack stats in development mode,
        # not everyone sets this setting, so let's assume it's production.
        if debug:
            app.before_request(self._refresh_webpack_stats)

        if hasattr(app, "add_template_global"):
            app.add_template_global(self.javascript_tag)
            app.add_template_global(self.stylesheet_tag)
            app.add_template_global(self.asset_urls_for)
            # for backwards compatibility
            app.add_template_global(self.asset_url_for)
        else:
            # Flask < 0.10
            ctx = {
                "javascript_tag": self.javascript_tag,
                "stylesheet_tag": self.stylesheet_tag,
                "asset_urls_for": self.asset_urls_for,
            }
            app.context_processor(lambda: ctx)

    def _set_asset_paths(self, app: Flask):
        """
        Read in the manifest.json file which acts as a manifest for assets.
        This allows us to get the asset path as well as hashed names.

        :param app: Flask application
        :return: None
        """
        webpack_stats = app.config.get(
            "WEBPACK_MANIFEST_PATH", self.manifest_path
        )
        if webpack_stats is None:
            self.log("[Flask-Webpack] 'WEBPACK_MANIFEST_PATH' is not set")
        else:
            try:
                with app.open_resource(webpack_stats, "r") as stats_json:
                    stats = json.load(stats_json)

                self.assets_url = (
                    app.config.get("WEBPACK_ASSETS_URL")
                    or stats.get("publicPath")
                    or stats.get("public_path")
                    or self.assets_url
                    or ""
                )
                self.assets = stats.get("assets") or stats
            except IOError:
                message = (
                    "[Flask-Webpack] WEBPACK_MANIFEST_PATH='{}' must point to"
                    " a valid json file."
                ).format(webpack_stats)
                self.log(message)
                if self.log_level == "ERROR":
                    raise RuntimeError(message)

    def _refresh_webpack_stats(self) -> None:
        """
        Refresh the webpack stats so we get the latest version. It's a good
        idea to only use this in development mode.

        :return: None
        """
        self._set_asset_paths(current_app)

    def _warn_missing(self, missing: str, type_info: str = "asset") -> Markup:
        """
        :param missing: the str asset name that was not found in self.assets
        :param type_info: the type of asset that is missing (e.g. "script").
        """
        return _warn_missing(
            missing,
            type_info,
            level=self.log_level,
            log=self.log,
            values=self.assets,
        )

    @contextfunction
    def javascript_tag(
        self, ctx, *assets: ChunkDef, unique: bool = True, **attrs: JsonValue
    ) -> Markup:
        """
        Convenience tag to output 1 or more javascript tags.

        :param args: 1 or more javascript file names
        :param unique: bool whether the tag should describe a unique resource
        :param attrs: dict <script> tag attr name-value pairs
        :return: Script tag(s) with the named attrs containing the named asset
        """
        _attrs = _get_attrs(attrs)
        tags = []

        def make_tag(chunk_url):
            tag_attrs = _markup_kvp(**_attrs)  # type: str
            tags.append(
                '<script src="{}" {}></script>'.format(chunk_url, tag_attrs)
            )

        all_chunk_urls = []  # type: List[ChunkDef]
        for asset in assets:
            chunk_urls = self.resolve_ext(asset, extensions=["", ".js"])
            if chunk_urls:
                all_chunk_urls += chunk_urls
            else:
                tags.append(self._warn_missing(asset, "script"))
        for_each_unique_chunk(ctx, all_chunk_urls, make_tag, unique=unique)
        return Markup("\n".join(tags))

    @contextfunction
    def stylesheet_tag(self, ctx, *assets, **attrs):
        """
        Convenience tag to output 1 or more stylesheet tags.

        :param assets: 1 or more names of bundled stylesheets.
        :param unique: bool whether the tag should describe a unique resource
        :param attrs: properties to be applied to all the output html elements
        :return: Markdown <link rel="stylesheet" .../>s containing the named
            assets
        """
        tags = []
        unique = attrs.pop("unique", True)
        attrs = _merge({"rel": "stylesheet"}, _get_attrs(attrs))

        def make_tag(url):
            tag = '<link href="{}" {}>'.format(url, _markup_kvp(**attrs))
            tags.append(tag)

        all_chunk_urls = []
        for asset in assets:
            # ordered by how frequency of extension occurence.
            chunks = self.resolve_ext(
                asset, ["", ".css", ".scss", ".sass", ".less", ".styl"]
            )
            if chunks:
                all_chunk_urls += chunks
            else:
                tags.append(self._warn_missing(asset, "stylesheet"))
        for_each_unique_chunk(ctx, all_chunk_urls, make_tag, unique=unique)

        return Markup("\n".join(tags))

    def asset_urls_for(self, asset):
        """
        Look up the hashed asset path of a bundle name unless it starts with
        something that resembles a web address. In that case, interpret the
        bundle name as a URL.

        :param asset: A logical path to an asset
        :type asset: str
        :return: List[str] a list of string paths or None if not found
        """
        if "//" in asset:
            return asset

        if asset not in self.assets:
            return None

        packed_asset = self.assets[asset]
        if type(packed_asset) is not list and type(packed_asset) is not tuple:
            packed_asset = [packed_asset]
        return [(self.assets_url or "") + chunk for chunk in packed_asset]

    def asset_url_for(self, asset, warn_multiple=True):
        """Get one url for an asset name.

        :param asset: str the name of the asset.
        :param warn_multiple: bool whether to warn if multiple chunks retreived.

        :return: Description of returned object.
        """
        resolved = self.asset_urls_for(asset)
        if resolved:
            if len(resolved) == 1:
                return Markup(resolved[0])
            elif warn_multiple:
                return _warn_multiple(
                    asset,
                    level=self.log_level,
                    log=self.log,
                    values=self.assets,
                )

    def resolve_ext(self, asset: ChunkDef, extensions=[""]) -> ChunkDef:
        """Find the first asset in the manifest

        :param asset: str the start of an asset name
        :param extensions: List[str] extensions to check

        :return: List[str] the list of chunk urls associated with the asset
        """
        for ext in extensions:
            resolved = self.asset_urls_for(asset + ext)
            if resolved:
                return resolved
        return ""
