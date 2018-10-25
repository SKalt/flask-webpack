import pytest
from flask_webpack import (
    _markup_kvp,
    _warn_missing,
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


def test_markup_kvp():
    assert _markup_kvp(a=True) == 'a'
    assert _markup_kvp(b=False) == ''
    assert _markup_kvp(c='d') == 'c="d"'
