import pytest
from flask import (
    Flask,
    render_template_string,
)
from flask_webpack import (
    _markup_kvp,
    _warn_missing,
    Webpack,
)

msg = '[flask-webpack] missing asset name'


@pytest.mark.parametrize('level,expected', [
    ('DEBUG', '<!-- ' + msg + ' -->'),
    ('INFO', '<script>console.info("' + msg + '")</script>'),
    ('WARNING', '<script>console.warn("' + msg + '")</script>'),
    ('ERROR', '<script>console.error("' + msg + '")</script>'),
    ('CRITICAL', '<script>alert("' + msg + '")</script>'),
])
def test_warn_missing(level, expected):

    def message_logged(generated):
        assert \
            generated == msg, \
            'incorrect warning message logged at level ' + level

    _warn_missing(
        'name',
        'asset',
        level,
        message_logged
    )

    assert _warn_missing('name', level=level) == expected, 'unexpected warning'


def test_warn_missing_js_bundle():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string(
            '{{ javascript_tag("foo", module=True) }}'
        )
    expected = (
        '<script>console.info("[flask-webpack] missing script foo")</script>'
    )
    assert rendered == expected


def test_markup_kvp():
    assert _markup_kvp(a=True) == 'a'
    assert _markup_kvp(b=False) == ''
    assert _markup_kvp(c='d') == 'c="d"'


def test_asset_url_for():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', foo="foo.h4sh3d.js")
    with app.app_context():
        rendered = render_template_string('{{ asset_url_for("foo") }}')
    assert rendered == '/foo.h4sh3d.js'


def test_js_tag_basic():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', foo="foo.h4sh3d.js")
    with app.app_context():
        rendered = render_template_string('{{ javascript_tag("foo") }}')
    assert rendered == '<script src="/foo.h4sh3d.js" ></script>'


def test_js_tag_multiple():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', foo="foo.h4sh3d.js", bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string('{{ javascript_tag("foo", "bar") }}')
    expected = (
        '<script src="/foo.h4sh3d.js" ></script>\n'
        '<script src="/bar.11a6e2.js" ></script>'
    )
    assert rendered == expected


def test_js_tag_multiple_kvp():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', foo="foo.h4sh3d.js", bar="bar.11a6e2.js")
    with app.app_context():
        rendered = render_template_string(
            '{{ javascript_tag("foo", "bar", async=True, defer=True) }}'
        )
    expected = (
        '<script src="/foo.h4sh3d.js" async defer></script>\n'
        '<script src="/bar.11a6e2.js" async defer></script>'
    )
    assert rendered == expected


def test_style_tag_multiple_kvp():
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', foo="foo.h4sh3d.css", bar="bar.11a6e2.css")
    with app.app_context():
        rendered = render_template_string(
            '{{ stylesheet_tag('
            '"foo", "bar", crossorigin="anonymous", type="text/css"'
            ') }}'
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
    assert rendered == expected


@pytest.mark.parametrize('ext', ('.scss', '', '.sass', '.less', '.styl'))
def test_style_preprocessor(ext):
    app = Flask('test_app')
    # app.config['WEBPACK_MANIFEST_PATH'] = ''
    app.config['WEBPACK_LOG_LEVEL'] = 'INFO'
    Webpack(app, assets_url='/', **{"foo{}".format(ext): "foo.h4sh3d.css"})
    with app.app_context():
        rendered = render_template_string(
            '{{ stylesheet_tag('
            '"foo", crossorigin="anonymous", type="text/css"'
            ') }}'
        )
    expected = (
            '<link rel="stylesheet"'
            ' href="/foo.h4sh3d.css"'
            ' crossorigin="anonymous"'
            ' type="text/css">'
    )
    assert rendered == expected