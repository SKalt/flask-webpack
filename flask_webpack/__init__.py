import os
import json

from flask import current_app
from jinja2 import Markup
from logging import getLevelName


def _noop(*args, **kwargs):
    pass

def _escape(s):
    return (
        s.replace("&", "&amp;")
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def _markup_kvp(**attrs):
    """helper: returns str HTML-style key-value pairs"""
    return " ".join(
        [
            key if value is True else '{}="{}"'.format(
                key, _escape(str(value))
            )
            for key, value in attrs.items()
            if value is not False
        ]
    )


def _warn_missing(missing, type_info="asset", level="ERROR", log=_noop):
    message = "[flask-webpack] missing {type_info} {missing}".format(
        type_info=type_info, missing=missing
    )
    log(message)

    def js_warn(fn, msg):
        msg = msg.replace('"', '\\"')  # escape double qotes for JS safety
        return '<script>{fn}("{msg}")</script>'.format(fn=fn, msg=msg)

    if level == "DEBUG":
        return "<!-- {} -->".format(message.replace("-->", ""))
    elif level == "INFO":
        return js_warn("console.info", message)
    elif level == "WARNING":
        return js_warn("console.warn", message)
    elif level == "ERROR":
        return js_warn("console.error", message)
    elif level == "CRITICAL":
        return js_warn("alert", message)
    else:
        return ""


class Webpack(object):
    def __init__(
        self, app=None, assets_url=None, manifest_path=None, **assets
    ):
        """
        Internalize the app context and add helpers to the app.
        :param app: the flask app
        :param assets_url: a URL to prefex all assets with
        :param manifest_path: the path to a JSON name/filename asset map
        :param assets: a JSON name/filename asset map
        """
        self.app = app
        self.assets_url = assets_url
        self.assets = assets
        self.manifest_path = manifest_path
        if app is not None:
            self.init_app(app)
        else:
            self.log_level = "ERROR"
            self.log = _noop

    def init_app(self, app):
        """
        Mutate the application passed in as explained here:
        http://flask.pocoo.org/docs/latest/extensiondev/

        :param app: Flask application
        :return: None
        """
        debug = (
            app.config.get("DEBUG")
            or os.environ.get("FLASK_DEBUG")
            or os.environ.get("FLASK_ENV") == 'development'
        )
        log_level = app.config.get(
            "WEBPACK_LOG_LEVEL", "DEBUG" if debug else "ERROR"
        )

        def log(message):
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
            app.add_template_global(self.asset_url_for)
        else:
            # Flask < 0.10
            ctx = {
                "javascript_tag": self.javascript_tag,
                "stylesheet_tag": self.stylesheet_tag,
                "asset_url_for": self.asset_url_for,
            }
            app.context_processor(lambda: ctx)

    def _set_asset_paths(self, app):
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

    def _refresh_webpack_stats(self):
        """
        Refresh the webpack stats so we get the latest version. It's a good
        idea to only use this in development mode.

        :return: None
        """
        self._set_asset_paths(current_app)

    def _warn_missing(self, missing, type_info="asset"):
        """
        :param missing: the str asset name that was not found in self.assets
        :param type_info: the type of asset that is missing (e.g. "script").
        """
        return _warn_missing(
            missing, type_info, level=self.log_level, log=self.log
        )

    def javascript_tag(self, *args, **attrs):
        """
        Convenience tag to output 1 or more javascript tags.

        :param args: 1 or more javascript file names
        :return: Script tag(s) containing the asset
        """
        tags = []

        for arg in args:
            asset_path = self.asset_url_for(
                "{}.js".format(arg)
            ) or self.asset_url_for(arg)
            if asset_path:
                tags.append(
                    '<script src="{}" {}></script>'.format(
                        asset_path, _markup_kvp(**attrs)
                    )
                )
            else:
                tags.append(self._warn_missing(arg, "script"))
        return Markup("\n".join(tags))

    def stylesheet_tag(self, *assets, **attrs):
        """
        Convenience tag to output 1 or more stylesheet tags.

        :param assets: 1 or more names of bundled stylesheets.
        :param attrs: properties to be applied to all the output html elements
        :return: Markdown <link rel="stylesheet" .../>s containing the named
            assets
        """
        tags = []

        for asset in assets:
            asset_path = (
                # ordered by how frequency of extension occurence.
                self.asset_url_for("{}.css".format(asset))
                or self.asset_url_for(asset)
                or self.asset_url_for("{}.scss".format(asset))
                or self.asset_url_for("{}.sass".format(asset))
                or self.asset_url_for("{}.less".format(asset))
                or self.asset_url_for("{}.styl".format(asset))
            )
            if asset_path:
                tags.append(
                    '<link rel="stylesheet" href="{0}" {1}>'.format(
                        asset_path, _markup_kvp(**attrs)
                    )
                )
            else:
                tags.append(self._warn_missing(asset, "stylesheet"))

        return Markup("\n".join(tags))

    def asset_url_for(self, asset):
        """
        Look up the hashed asset path of a bundle name unless it starts with
        something that resembles a web address. In that case, interpret the
        bundle name as a URL.

        :param asset: A logical path to an asset
        :type asset: str
        :return: str asset path or None if not found
        """
        if "//" in asset:
            return asset

        if asset not in self.assets:
            return None

        return "{0}{1}".format(self.assets_url, self.assets[asset])
