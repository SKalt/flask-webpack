import pytest
import os
import sys
from flask import Flask, render_template_string
from werkzeug.routing import BuildError
from flask_asset_map import _markup_kvp, _get_attrs, _warn_missing, AssetMap
from lxml.etree import fromstring, XMLParser

# constants
parser = XMLParser(recover=True)
msg = "[flask-asset-map] missing asset name"


def parse(e):
    """Turn a string html element into a dict of tag attributes"""
    return fromstring(e, parser=parser).attrib


def check_attrib(rendered, expected):
    version = float(sys.version[:2])
    if version >= 3.6:
        assert rendered == expected
    else:
        for actual, target in zip(rendered.split("\n"), expected.split("\n")):
            expected_props = parse(target)
            actual_props = parse(actual)
            assert expected_props == actual_props


@pytest.mark.parametrize(
    "test_input, expected",
    [({"attrs": {"async": True}, "ff": "bb"}, {"async": True, "ff": "bb"})],
)
def test_attr_resolution(test_input, expected):
    assert _get_attrs(test_input) == expected


@pytest.mark.parametrize(
    "level,expected",
    [
        ("DEBUG", "<!-- " + msg + " -->"),
        ("INFO", '<script>console.warn("' + msg + '")</script>'),
        ("WARNING", '<script>console.error("' + msg + '")</script>'),
    ],
)
def test_warn_missing(level, expected):
    def message_logged(generated):
        assert generated == msg, (
            "incorrect warning message logged at level " + level
        )

    _warn_missing("name", "asset", level, message_logged)

    assert _warn_missing("name", level=level) == expected, "unexpected warning"


@pytest.mark.parametrize("level", ("ERROR", "CRITICAL"))
def test_warn_missing_throws(level):
    def message_logged(generated):
        assert generated == msg, (
            "incorrect warning message logged at level " + level
        )

    bad_asset_map = {"is it": "me you're looking for?"}
    with pytest.raises(BuildError) as err_info:
        _warn_missing(
            "name",
            "asset",
            level="ERROR",
            log=message_logged,
            values=bad_asset_map,
        )
        assert False, "Should have thrown a BuildError"
    err = err_info.value
    assert err.method == ("asset",), "incorrect error method"
    assert err.values == bad_asset_map
    assert err.args == ("name", bad_asset_map, ("asset",))


def test_warn_missing_js_bundle():
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string(
            '{{ javascript_tag("foo", module=True) }}'
        )
    expected = (
        '<script>console.warn("[flask-asset-map] missing script foo")</script>'
    )
    assert rendered == expected


def test_markup_kvp():
    assert _markup_kvp(a=True) == "a"
    assert _markup_kvp(b=False) == ""
    assert _markup_kvp(c="d") == 'c="d"'


def test_asset_url_for():
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", foo="foo.h4sh3d.js")
    with app.app_context():
        rendered = render_template_string('{{ asset_url_for("foo") }}')
    assert rendered == "/foo.h4sh3d.js"


def test_js_tag_basic():
    app = Flask("test_app")
    app.config["ASET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", foo="foo.h4sh3d.js")
    with app.app_context():
        rendered = render_template_string('{{ javascript_tag("foo") }}')
    assert rendered == '<script src="/foo.h4sh3d.js" ></script>'


def test_js_tag_multiple():
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", foo="foo.h4sh3d.js", bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string('{{ javascript_tag("foo", "bar") }}')
    expected = (
        '<script src="/foo.h4sh3d.js" ></script>\n'
        '<script src="/bar.11a6e2.js" ></script>'
    )
    check_attrib(rendered, expected)


def test_js_tag_multiple_kvp():
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", foo="foo.h4sh3d.js", bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string(
            '{{ javascript_tag("foo", "bar",'
            ' attrs={"async": True}, defer=True) }}'
        )
    expected = (
        '<script src="/foo.h4sh3d.js" async defer></script>\n'
        '<script src="/bar.11a6e2.js" async defer></script>'
    )
    check_attrib(rendered, expected)


def test_style_tag_multiple_kvp():
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", foo="foo.h4sh3d.css", bar="bar.11a6e2.css")
    with app.app_context():
        rendered = render_template_string(
            "{{ stylesheet_tag("
            '"foo", "bar", crossorigin="anonymous", type="text/css"'
            ") }}"
        )
    expected = (
        '<link rel="stylesheet"'
        ' href="/foo.h4sh3d.css"'
        ' crossorigin="anonymous"'
        ' type="text/css">\n'
        '<link rel="stylesheet"'
        ' href="/bar.11a6e2.css"'
        ' crossorigin="anonymous"'
        ' type="text/css">'
    )
    check_attrib(rendered, expected)


@pytest.mark.parametrize("ext", (".scss", "", ".sass", ".less", ".styl"))
def test_style_preprocessor(ext):
    app = Flask("test_app")
    app.config["ASSET_MAP_LOG_LEVEL"] = "INFO"
    AssetMap(app, assets_url="/", **{"foo{}".format(ext): "foo.h4sh3d.css"})
    with app.app_context():
        rendered = render_template_string(
            "{{ stylesheet_tag("
            '"foo", crossorigin="anonymous", type="text/css"'
            ") }}"
        )
    expected = (
        '<link rel="stylesheet"'
        ' href="/foo.h4sh3d.css"'
        ' crossorigin="anonymous"'
        ' type="text/css">'
    )
    check_attrib(rendered, expected)


__dirname = os.path.dirname(os.path.abspath(__file__))


def test_nested_asset_map():
    path = os.path.abspath(
        os.path.join(__dirname, "test_app_wp1", "build", "manifest.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    AssetMap(app)
    with app.app_context():
        r1 = render_template_string(
            '{{ asset_url_for("images/dog/no-idea.jpg") }}'
        )
        r2 = render_template_string('{{ asset_url_for("app_js.js") }}')
    e1 = (
        "http://localhost:2992/assets/images/dog/"
        "no-idea.b9252d5fd8f39ce3523d303144338d7b.jpg"
    )
    e2 = "http://localhost:2992/assets/app_js.8b7c0de88caa3f366b53.js"
    assert r1 == e1
    assert r2 == e2


def test_nested_asset_map_missing_public_path():
    path = os.path.abspath(
        os.path.join(__dirname, "nested_asset_map_missing_public_path.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    asset_map = AssetMap()
    asset_map.init_app(app)
    with app.app_context():
        rendered = render_template_string('{{ asset_url_for("temp.js") }}')
    assert rendered == "//localhost:8080/temp.js"


def test_flat_asset_map_renamed_public_path():
    path = os.path.abspath(
        os.path.join(__dirname, "flat_asset_map_renamed_public_path.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    asset_map = AssetMap()
    asset_map.init_app(app)

    with app.app_context():
        r1 = render_template_string('{{ asset_url_for("foo") }}')
        r2 = render_template_string('{{ asset_url_for("bar.js") }}')
    e1 = "//localhost:8080/foo.h4sh3d.js"
    e2 = "//localhost:8080/completely-different.hashed.js"
    assert r1 == e1
    assert r2 == e2


def test_flat_asset_map():
    path = os.path.abspath(
        os.path.join(__dirname, "complete_flat_asset_map.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    AssetMap(app)
    with app.app_context():
        r1 = render_template_string("{{ javascript_tag('foo') }}")
        r2 = render_template_string("{{ javascript_tag('bar.js') }}")
    e1 = '<script src="correct/foo.h4sh3d.js" ></script>'
    e2 = '<script src="correct/completely-different.hashed.js" ></script>'
    assert r1 == e1
    assert r2 == e2


def test_flat_asset_map_missing_public_path():
    path = os.path.abspath(
        os.path.join(__dirname, "flat_asset_map_missing_public_path.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    app.config["ASSETS_URL"] = "correct/"
    AssetMap(app)
    with app.app_context():
        r1 = render_template_string("{{ javascript_tag('foo') }}")
        r2 = render_template_string("{{ javascript_tag('bar.js') }}")
    e1 = '<script src="correct/foo.h4sh3d.js" ></script>'
    e2 = '<script src="correct/completely-different.hashed.js" ></script>'
    assert r1 == e1
    assert r2 == e2


def test_chunked_asset_map():
    path = os.path.abspath(
        os.path.join(__dirname, "flat_chunked_asset_map.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    app.config["ASSETS_URL"] = "correct/"
    AssetMap(app)
    with app.app_context():
        r1 = render_template_string(
            '{{ javascript_tag("vendor~jquery", defer=True) }}'
        )
        r2 = render_template_string(
            "{{ javascript_tag('foo', attrs={'defer': True}) }}"
        )
        r3 = render_template_string(  # TODO: ///
            "{{ javascript_tag('bar.js', attrs={'async': True}) }}"
        )
    e1 = '<script src="correct/vendor~jquery.ch0nk3d.js" defer></script>'
    e2 = e1 + '\n<script src="correct/foo.h4sh3d.js" defer></script>'
    e3 = (
        e1.replace("defer", "async")
        + '\n<script src="correct/completely-different.hashed.js" async></script>'
    )
    assert r1 == e1
    assert r2 == e2
    assert r3 == e3


def test_chunked_asset_map_deduped():
    path = os.path.abspath(
        os.path.join(__dirname, "flat_chunked_asset_map.json")
    )
    app = Flask("test_app")
    app.config["ASSET_MAP_PATH"] = path
    app.config["ASSETS_URL"] = "correct/"
    AssetMap(app)
    with app.app_context():
        # r1, r2 are equivalent: both test that the vendor chunk is deduped
        r1 = render_template_string("{{ javascript_tag('foo', 'bar') }}")
        r2 = render_template_string(
            "{{ javascript_tag('foo') }}\n{{ javascript_tag('bar') }}"
        )
        # still, you should be able to duplicate chunks if you need.
        r3 = render_template_string(
            "{{ javascript_tag('vendor~jquery', unique=False) }}"
            "{{ javascript_tag('vendor~jquery', unique=False) }}"
        )
    vendor = '<script src="correct/vendor~jquery.ch0nk3d.js" ></script>'
    foo = '<script src="correct/foo.h4sh3d.js" ></script>'
    bar = '<script src="correct/completely-different.hashed.js" ></script>'
    assert r1 == r2
    assert r1 == "\n".join((vendor, foo, bar))
    assert r3 == vendor + vendor
