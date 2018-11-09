<h1 align="center"> Flask-Webpack</h1>

<p align="center">
<a href="https://pypi.org/project/Flask-Webpack/"><img alt="PyPI" src="https://img.shields.io/pypi/v/flask-webpack.svg"/>
<a href="https://pypi.org/project/Flask-Webpack/"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/flask-webpack.svg"></a>
<a href="https://travis-ci.org/nickjj/flask-webpack?branch=master"><img alt="build status" src="https://travis-ci.org/nickjj/flask-webpack.svg?branch=master"/></a>
<a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a>

>  Manage frontend assets with [Webpack](https://webpack.js.org/>), use them with flask

</p>

Webpack can produce hashed asset bundles ( like `index.bundle.md5h4sh3d.js` ). Flask-Webpack provides global jinja2 templates that look up your your hashed bundles by name in an asset map.


Installation
------------

```{sh}
pip install flask-webpack # from pypi
# or
pip install git+https://github.com/nickjj/flask-webpack#egg=flask_webpack
```

<details><summary><span style="font-size: 24px; font-weight: 600;">Quickstart</span></summary>

```{sh}
  # webpack quickstart
  npm install --save-dev webpack webpack-cli webpack-manifest-plugin
  npm install --save lodash
  npx webpack \
    --output-filename [name].[chunkhash].js \
    --plugin webpack-manifest-plugin
  # looks for ./src/index.js for js assets, puts their compiled results in
  # ./dist/
```
```{javascript}
// src/index.js
import _ from 'lodash'
console.log(_.join(['hello', 'webpack'], ' '))
```
```python
# app.py
from flask import Flask
from flask_webpack import Webpack

webpack = Webpack()

app = Flask(__name__, static_folder="./dist")
webpack.init_app(app)
```
```HTML
<!-- templates/index.html -->
{{ javascript_tag("index.js") }}
```

If you have a webpack entrypoint named ``index.js``, the template will complile to

```{HTML}
  <script src="index.h4sh3d.js"></script>
```

Now you can happily tell your frontend proxy to cache that hamburger image for
an entire year. If you ever change the hamburger, the md5 will change but you
do not need to change any of your templates because the `asset_url_for`
tag knows how to look it up.
</details>

<details><summary><span style="font-size: 24px; font-weight: 600;">Global template tags</span></summary>

| tag | results|
|--|--|
`asset_url_for(asset_name)` | resolves an asset name. Quotes not included.
`javascript_tag(*asset_names, **tag_props)` | produces a `<script>` tag for each passed asset name.
`stylesheet_tag(*asset_names, **tag_props)` | writes out a `<link rel="stylesheet">` tag for each passed asset.

You can view a complete working example in the <a href="./flask_webpack/tests/test_app">test app</a>.

There's also a <a href="https://nickjanetakis.com/blog/manage-your-assets-with-flask-webpack">blog post and short video</a> explaining how to use this extension.
</details>

<details>
  <summary><span style="font-size: 20px; font-weight: 600;">Building your asset map</span>
  </summary>
Flask-Webpack requires a JSON file `manifest.json` mapping the name of each of your bundles to its hashed equivalent. You can build this manifest file using
<a
  href="https://www.npmjs.com/package/webpack-manifest-plugin">
  <code>webpack-manifest-plugin</code></a>
or
<a  href="https://github.com/nickjj/manifest-revision-webpack-plugin">
  <code>manifest-revision-plugin</code></a>
</a>
</details>


<details>
<summary><span style="font-size: 20px; font-weight: 600;">Configuration<span></summary>

`Flask-Webpack` resolves its configuration options with this order of priority:
  1. `app.config[OPTION_NAME]` trumps all
  2. a named option in the asset_map
  3. `flask_webpack.Webpack(**{"option_name": option_value})`

Here are the available configuration options:


```python
(
  app.config["WEBPACK_MANIFEST_PATH"]
  or flask_webpack.Webpack(manifest_path=None)
)
```
default: ``None``

**Required:** any valid path to a JSON asset map. An idiomatic location might be  `./dist/manifest.json` relative to your `package.json`.

```python
(
  app.config["WEBPACK_ASSETS_URL"]
  or json_asset_map["publicPath"]
  or json_asset_map["public_path"]
  or flask_webpack.Webpack(assets_url=None)
)
```
default: `"/"`

**Optional:** A URL to prepend to your hashed asset names. In production, you can set this to your full domain name or CDN.  In development, you might to point to a [`webpack-dev-server`](https://github.com/webpack/webpack-dev-server) on another port.  You can control this in python switching `os.environ.get("FLASK_ENV") == "development"` or by changing the value of the `publicPath` key in the generation of your asset map.

⚠️ warning: this does not automatically join the URL and your asset name.  You must provide the joining `/`.

⚠️ warning: prepending a different `asset_url`/`public_path` to your assets may cause them not to work in production `url(./relative/path/to/style/asset)`


```python
app.config.get("WEBPACK_MANIFEST_ASSETS_ONLY")
```
default: ``False``

**Optional:** Assume the manifest file only contains the assets and *not* `"publicPath"` or `"public_path"`. Otherwise, `flask_webpack` will handle both flat asset maps and asset maps with an `"asset"` key.

```python
(
  app.config.get("WEBPACK_LOG_LEVEL")
  or 'DEBUG' if (
    os.environ.get("FLASK_DEBUG")
    or os.environ.get("FLASK_ENV") == 'development'
  )
  else 'ERROR'
)
```
default: `"ERROR"`
**Optional** One of the .string [python logging levels](https://docs.python.org/3/howto/logging.html#logging-levels).  The higher/more serious the level, more visible a missing asset will become.

|error level| missing asset yields|
|--|--|
|**DEBUG**| `<-- comment about missing asset -->`|
if level == "DEBUG":
    return "<!-- {} -->".format(message.replace("-->", "")
|**INFO**|`console.warn`|
|**WARNING**|`console.error`|
|**ERROR+**|`werkzeug.routing.BuildError`|

</details>

<details><summary>Development</summary>

```sh
git clone https://github.com/nickjj/flask-webpack.git
cd flask-webpack

# having created a fresh virtualenv with a tool of your choice..
source activate flask-webpack
pip install -r requirements.txt
pip install -r devRequirements.txt
```
pre-push, please run:
```bash
flake8 .      # check the style
pip install . # check it builds
pyre check    # run the static type checker
pytest ./tests/unit.py ./tests/test_app_wp1/tests
pip uninstall flask-webpack
```
</details>

### Contributors

- Nick Janetakis <nick.janetakis@gmail.com>
