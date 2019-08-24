from flask import Flask, render_template
from werkzeug.serving import run_simple

from flask_asset_map import AssetMap

asset_map = AssetMap()


def create_app(settings_override=None):
    """
    Create a test application.

    :param settings_override: Override settings
    :type settings_override: dict
    :return: Flask app
    """
    app = Flask(__name__)

    params = {"DEBUG": True, "ASSET_MAP_PATH": "./build/manifest.json"}

    app.config.update(params)

    if settings_override:
        app.config.update(settings_override)

    asset_map.init_app(app)

    return app


app = create_app()


@app.route("/")
def index():
    return render_template("index.jinja2")


if __name__ == "__main__":
    run_simple("localhost", 5000, app, use_reloader=True, use_debugger=True)
