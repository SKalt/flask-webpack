import json

from flask import current_app
from jinja2 import Markup
from logging import getLevelName


def _noop(*args, **kwargs):
    pass


def _markup_kvp(**attrs):
    return " ".join(
        [
            key if value is True else '{}="{}"'.format(key, value)
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
        return Markup("<!-- {} -->".format(message.replace("-->", "")))
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
    def __init__(self, app=None, assets_url=None, **assets):
        """Internalize the app context and add helpers to the app."""
        self.app = app
        self.assets_url = assets_url
        self.assets = assets
        if app is not None:
            self.init_app(app)
        else:
            self.log_level = "ERROR"
            self.log = _noop

    def init_app(self, app):
        """
        Mutate the application passed in as explained here:
        http://flask.pocoo.org/docs/0.12/extensiondev/

        :param app: Flask application
        :return: None
        """

        # Setup a few sane defaults.
        app.config.setdefault(
            "WEBPACK_MANIFEST_PATH",
            "/tmp/themostridiculousimpossiblepathtonotexist",
        )
        app.config.setdefault("WEBPACK_ASSETS_URL", None)
        self._set_asset_paths(app)

        # We only want to refresh the webpack stats in development mode,
        # not everyone sets this setting, so let's assume it's production.
        debug = app.config.get("DEBUG", False)
        if debug:
            app.before_request(self._refresh_webpack_stats)

        log_level = app.config.get(
            "WEBPACK_LOG_LEVEL", "DEBUG" if debug else "ERROR"
        )

        def log(message):
            app.logger.log(getLevelName(log_level), message)

        if log_level:
            self.log_level = log_level
            self.log = log

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
        Read in the manifest json file which acts as a manifest for assets.
        This allows us to get the asset path as well as hashed names.

        :param app: Flask application
        :return: None
        """
        webpack_stats = app.config.get("WEBPACK_MANIFEST_PATH")
        if webpack_stats is None:
            self.log("[Flask-Webpack] 'WEBPACK_MANIFEST_PATH' is not set")
        else:
            try:
                with app.open_resource(webpack_stats, "r") as stats_json:
                    stats = json.load(stats_json)
                    public_path = "/"

                    if app.config.get("WEBPACK_MANIFEST_ASSETS_ONLY") is True:
                        self.assets = stats
                    else:
                        self.assets = stats["assets"]
                        public_path = stats.get("publicPath") or public_path

                    self.assets_url = (
                        app.config.get("WEBPACK_ASSETS_URL") or public_path
                    )
            except IOError:
                message = (
                    "[Flask-Webpack] WEBPACK_MANIFEST_PATH "
                    "{} must point to a valid json file.".format(webpack_stats)
                )
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
            asset_path = self.asset_url_for("{}.js".format(arg))
            if asset_path:
                tags.append(
                    Markup(
                        '<script src="{}" {}></script>'.format(
                            asset_path, attrs
                        )
                    )
                )
            else:
                tags.append(self._warn_missing(arg, "script"))
        return "\n".join(tags)

    def stylesheet_tag(self, *args, **attrs):
        """
        Convenience tag to output 1 or more stylesheet tags.

        :param args: 1 or more stylesheet file names
        :return: Link tag(s) containing the asset
        """
        tags = []

        for arg in args:
            asset_path = self.asset_url_for("{0}.css".format(arg))
            if asset_path:
                tags.append(
                    Markup(
                        '<link rel="stylesheet" href="{0}">'.format(
                            asset_path, _markup_kvp(**attrs)
                        )
                    )
                )
            else:
                tags.append(self._warn_missing(arg, "stylesheet"))

        return Markup("\n".join(tags))

    def asset_url_for(self, asset):
        """
        Lookup the hashed asset path of a file name unless it starts with
        something that resembles a web address, then take it as is.

        :param asset: A logical path to an asset
        :type asset: str
        :return: Asset path or None if not found
        """
        if "//" in asset:
            return asset

        if asset not in self.assets:
            return None

        return "{0}{1}".format(self.assets_url, self.assets[asset])
